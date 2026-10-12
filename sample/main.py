import os
import ast
import subprocess
import argparse
import time
from pathlib import Path
from threading import Semaphore, Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

from DOT import analyze, get_dep, format_dep, build_prompt
from LLM import LinguisticCore

sem = Semaphore(10)


class Analyzer:
    def __init__(self, target):
        self.target = Path(target)
        self.files = {}

    def scan(self):
        for f in self.target.rglob("*.py"):
            self.files[f.stem] = {"path": str(f), "members": self._parse(f)}
        if not self.files:
            return None
        return self._run_pyan()

    def _run_pyan(self):
        paths = [f['path'] for f in self.files.values()]
        quoted = ' '.join(f'"{p}"' for p in paths)
        cmd = f'pyan3 {quoted} --dot --no-defines --uses'
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return r.stdout if r.returncode == 0 else None
        except:
            return None

    def _parse(self, fpath):
        result = {"classes": {}, "functions": []}
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except SyntaxError:
            return result
        fname = fpath.stem
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                result["functions"].append({"key": f"{fname}__{node.name}", "name": node.name})
            elif isinstance(node, ast.ClassDef):
                cls = {"key": f"{fname}__{node.name}", "name": node.name, "methods": []}
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        cls["methods"].append({
                            "key": f"{fname}__{node.name}__{item.name}",
                            "name": f"{node.name}.{item.name}"
                        })
                result["classes"][node.name] = cls
        return result


def call_llm(args, msg):
    with sem:
        llm = LinguisticCore()
        llm.LLM_key = args.llm_key
        llm.LLM_url = args.llm_url
        llm.model = args.model
        llm.template = ''
        llm.web_search = False
        llm.call_robot = False
        llm.create_socket()
        if len(msg) > args.max_tokens:
            msg = msg[:args.max_tokens]
        with open("system.prompt", "r", encoding="utf-8") as f:
            sys_prompt = f.read()
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": msg}]
        for _ in range(5):
            try:
                return llm.process(messages, "solo")
            except Exception as e:
                time.sleep(2)
        return ""


def gen_doc(args, result):
    if not args.process:
        return ""
    return call_llm(args, build_prompt(result, args))


def gen_class_summary(args, cls_name, methods):
    if not args.process:
        return ""
    names = [m[3] for m in methods]
    prompt = f"Summarize class {cls_name} with methods: {', '.join(names)}. 1-2 sentences, in {args.language}."
    return call_llm(args, prompt)


def process_file(args, fname, finfo, nav, out_dir, target):
    rel = Path(finfo['path']).relative_to(target)
    info_path = out_dir / rel.with_suffix('.info')
    md_path = out_dir / rel.with_suffix('.md')
    info_path.parent.mkdir(parents=True, exist_ok=True)

    members = finfo['members']
    print(f"\n{fname}.py (classes: {len(members.get('classes', {}))}, funcs: {len(members.get('functions', []))})")

    tasks = []
    for cls_name, cls_info in members.get('classes', {}).items():
        for i, m in enumerate(cls_info['methods']):
            result = get_dep(nav, m['name'], m['key'], finfo['path'])
            if result and result.get("source_code"):
                tasks.append(((0, cls_name, i), result, m['name'], True, cls_name))

    for i, fn in enumerate(members.get('functions', [])):
        result = get_dep(nav, fn['name'], fn['key'], finfo['path'])
        if result and result.get("source_code"):
            tasks.append(((1, "", i), result, fn['name'], False, None))

    if not tasks:
        return None

    docs = {}
    lock = Lock()

    def worker(task):
        key, result, name, is_method, cls = task
        info = format_dep(result, args.relevant)
        md = gen_doc(args, result)
        print(f"  ✓ {name}")
        return key, info, md, name, is_method, cls

    with ThreadPoolExecutor(max_workers=10) as ex:
        for fut in as_completed([ex.submit(worker, t) for t in tasks]):
            try:
                key, info, md, name, is_method, cls = fut.result()
                with lock:
                    docs[key] = (info, md, name, is_method, cls)
            except Exception as e:
                print(f"  ✗ {e}")

    info_lines = []
    md_lines = [f"# {fname}.py\n\n**Path:** `{finfo['path']}`\n\n---\n\n"]
    stats = {"cls": 0, "func": 0, "method": 0}
    seen_cls = set()
    cur_cls = None
    has_func_header = False

    cls_docs = {}
    for key in sorted(docs.keys()):
        info, md, name, is_method, cls = docs[key]
        if is_method:
            cls_docs.setdefault(cls, []).append((key, info, md, name))

    for key in sorted(docs.keys()):
        info, md, name, is_method, cls = docs[key]
        if is_method:
            if cls != cur_cls:
                cur_cls = cls
                md_lines.append(f"## Class: `{cls}`\n\n")
                if cls in cls_docs:
                    summary = gen_class_summary(args, cls, cls_docs[cls])
                    if summary:
                        md_lines.append(f"> {summary.strip()}\n\n")
            if cls not in seen_cls:
                stats["cls"] += 1
                seen_cls.add(cls)
            stats["method"] += 1
        else:
            if not has_func_header:
                md_lines.append("## Functions\n\n")
                has_func_header = True
            stats["func"] += 1
        info_lines.append(info + "\n" + "=" * 50 + "\n\n")
        if md:
            md_lines.append(md + "\n\n")

    info_path.write_text("".join(info_lines), encoding="utf-8")
    md_path.write_text("".join(md_lines), encoding="utf-8")
    return stats


def main():
    p = argparse.ArgumentParser(description="CodeDoc - Auto Documentation Generator")
    p.add_argument('--target_path', type=str, required=True)
    p.add_argument('--output_dir', type=str, default=None)
    p.add_argument('--llm_key', type=str, default=os.getenv('LLM_KEY', ''))
    p.add_argument('--llm_url', type=str, default=os.getenv('LLM_URL', 'https://api.openai.com/v1'))
    p.add_argument('--model', type=str, default=os.getenv('MODEL', 'gpt-4o-mini'))
    p.add_argument('--max_tokens', type=int, default=10000)
    p.add_argument('--relevant', type=bool, default=True)
    p.add_argument('--process', type=bool, default=True)
    p.add_argument('--language', type=str, default="English")
    p.add_argument('--prompt_template', type=str, default='prompts/ISO.txt')
    args = p.parse_args()

    target = Path(args.target_path)
    out_dir = Path(args.output_dir) if args.output_dir else target / "docs"

    analyzer = Analyzer(str(target))
    dot = analyzer.scan()

    print(dot)
    exit()
    if not dot:
        print("Failed to analyze")
        return

    file_map = {k: v['path'] for k, v in analyzer.files.items()}
    nav = analyze(dot, str(target), file_map)

    total = {"cls": 0, "func": 0, "method": 0}
    for fname, finfo in analyzer.files.items():
        stats = process_file(args, fname, finfo, nav, out_dir, target)
        if stats:
            for k in total:
                total[k] += stats[k]

    print(f"\nOutput: {out_dir}")
    print(f"Classes: {total['cls']}, Methods: {total['method']}, Functions: {total['func']}")


if __name__ == "__main__":
    main()
