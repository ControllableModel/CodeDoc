import os
import ast
import subprocess
import argparse
import time
from pathlib import Path
from threading import Semaphore, Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

from codedoc.config import TEMPLATES, default_template
from codedoc.deps.dot import analyze, get_dep
from codedoc.writer.prompt import format_dep, build_prompt
from codedoc.writer.llm import LinguisticCore


def str2bool(value):
    """Parse a CLI boolean properly (argparse's bool() turns 'False' into True)."""
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    if v in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got: {value!r}")

sem = Semaphore(10)


def get_test_targets(target_path):
    """扫描tests文件夹，获取需要生成的文档目标（文件名 -> 源文件路径）"""
    target = Path(target_path)
    tests_dir = target / "tests"
    if not tests_dir.exists():
        return {}
    
    targets = {}
    for md_file in tests_dir.glob("*.md"):
        # md文件名对应源文件名，如 logger.md -> logger.py
        source_name = md_file.stem
        source_file = target / f"{source_name}.py"
        if source_file.exists():
            targets[source_name] = {
                "source": str(source_file),
                "output": str(md_file)
            }
    return targets


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
        # pyan is invoked in-process (not via subprocess) so that the
        # compatibility patch for pyan3's visit_AnnAssign crash applies; a
        # subprocess could not see the patch. See codedoc/deps/pyan_compat.py.
        from codedoc.deps.pyan_compat import preflight, run_pyan_dot
        try:
            return run_pyan_dot(paths)
        except RuntimeError as exc:
            print(f"pyan error: {exc}")
            print("  retrying with unparsable files excluded ...")
            bad = set(preflight(paths))
            if bad:
                print(f"  excluded {len(bad)} file(s): {sorted(bad)[:5]}")
            keep = [p for p in paths if p not in bad]
            if len(keep) == len(paths):
                raise
            return run_pyan_dot(keep)

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
        with open(str(TEMPLATES / "system.txt"), "r", encoding="utf-8") as f:
            sys_prompt = f.read()
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": msg}]
        for i in range(5):
            try:
                result = llm.process(messages, "solo")
                return result
            except Exception as e:
                print(f"  DEBUG: LLM attempt {i+1} failed: {e}")
                time.sleep(2)
        return ""


def gen_doc(args, result):
    if not args.process:
        print("  DEBUG: args.process is False")
        return ""
    try:
        response = call_llm(args, build_prompt(result, args))
        print(f"  DEBUG: LLM response len={len(response) if response else 0}")
        return response
    except Exception as e:
        print(f"  DEBUG: gen_doc exception: {e}")
        return ""


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
        print(f"  [OK] {name}")
        return key, info, md, name, is_method, cls

    with ThreadPoolExecutor(max_workers=10) as ex:
        for fut in as_completed([ex.submit(worker, t) for t in tasks]):
            try:
                key, info, md, name, is_method, cls = fut.result()
                with lock:
                    docs[key] = (info, md, name, is_method, cls)
            except Exception as e:
                print(f"  [ERROR] {e}")

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
    print(md_lines)
    info_path.write_text("".join(info_lines), encoding="utf-8")
    md_path.write_text("".join(md_lines), encoding="utf-8")
    return stats


def process_test_file(args, fname, finfo, output_path, nav):
    """处理单个测试文件，生成文档到指定的md文件"""
    members = finfo['members']
    source_path = finfo['path']
    
    print(f"\n{fname}.py (classes: {len(members.get('classes', {}))}, funcs: {len(members.get('functions', []))})")
    
    # 调试：打印 nav 中的节点
    print(f"  DEBUG: nav nodes = {list(nav.parser.nodes.keys())[:10]}...")
    
    tasks = []
    for cls_name, cls_info in members.get('classes', {}).items():
        for i, m in enumerate(cls_info['methods']):
            print(f"  DEBUG: checking method key={m['key']}, name={m['name']}")
            result = get_dep(nav, m['name'], m['key'], source_path)
            if result and result.get("source_code"):
                tasks.append(((0, cls_name, i), result, m['name'], True, cls_name))
            else:
                print(f"  DEBUG: no result for {m['key']}")

    for i, fn in enumerate(members.get('functions', [])):
        print(f"  DEBUG: checking func key={fn['key']}, name={fn['name']}")
        result = get_dep(nav, fn['name'], fn['key'], source_path)
        if result and result.get("source_code"):
            tasks.append(((1, "", i), result, fn['name'], False, None))
        else:
            print(f"  DEBUG: no result for {fn['key']}")

    if not tasks:
        print(f"  No tasks for {fname}")
        return None

    docs = {}
    lock = Lock()

    def worker(task):
        key, result, name, is_method, cls = task
        info = format_dep(result, args.relevant)
        md = gen_doc(args, result)
        print(f"  [OK] {name} (md_len={len(md) if md else 0})")
        return key, info, md, name, is_method, cls

    with ThreadPoolExecutor(max_workers=10) as ex:
        for fut in as_completed([ex.submit(worker, t) for t in tasks]):
            try:
                key, info, md, name, is_method, cls = fut.result()
                with lock:
                    docs[key] = (info, md, name, is_method, cls)
            except Exception as e:
                print(f"  [ERROR] {e}")

    md_lines = []
    for key in sorted(docs.keys()):
        info, md, name, is_method, cls = docs[key]
        if md:
            md_lines.append(md + "\n\n")

    # 写入到tests目录的md文件
    Path(output_path).write_text("".join(md_lines), encoding="utf-8")
    print(f"  -> {output_path}")
    return len(docs)


def main():
    p = argparse.ArgumentParser(description="CodeDoc - Auto Documentation Generator")
    p.add_argument('--target_path', type=str, required=True)
    p.add_argument('--output_dir', type=str, default=None)
    p.add_argument('--llm_key', type=str, default=os.getenv('LLM_KEY', ''),
                   help='LLM API key. Prefer the LLM_KEY environment variable (see .env.example).')
    p.add_argument('--llm_url', type=str, default=os.getenv('LLM_URL', 'https://api.openai.com/v1'),
                   help='OpenAI-compatible API base URL (env: LLM_URL).')
    p.add_argument('--model', type=str, default=os.getenv('MODEL', 'gpt-5-mini'))
    p.add_argument('--max_tokens', type=int, default=10000)
    p.add_argument('--relevant', type=str2bool, default=True,
                   help='Include dependency context (True/False).')
    p.add_argument('--process', type=str2bool, default=True,
                   help='Run the LLM generation stage (True/False).')
    p.add_argument('--language', type=str, default="English")
    p.add_argument('--prompt_template', type=str, default=default_template(),
                   help='Criteria template used for generation (default: ISO/IEC/IEEE 26514).')
    p.add_argument('--test_mode', action='store_true', help='只生成tests文件夹中已有md文件对应的文档')
    
    # Ablation study parameters
    p.add_argument('--ablation_mode', type=str, default='full', 
                   choices=['full', 'no_dep', 'no_prompt', 'baseline'],
                   help='Ablation study mode: full (default), no_dep (no dependencies), no_prompt (simple prompt), baseline (neither)')
    p.add_argument('--ablation_output', type=str, default=None,
                   help='Output directory for ablation experiments (default: output_dir/ablation_<mode>)')
    
    args = p.parse_args()

    # Never ship credentials in the source tree: the key must come from the
    # environment (LLM_KEY) or from an explicit CLI argument.
    if args.process and not args.llm_key:
        p.error("No LLM API key provided. Set the LLM_KEY environment variable "
                "(see .env.example) or pass --llm_key <your-key>. "
                "Use --process False to only run the static dependency analysis.")

    # Apply ablation settings
    if args.ablation_mode == 'no_dep':
        args.relevant = False
        print("Ablation Mode: NO DEPENDENCIES")
    elif args.ablation_mode == 'no_prompt':
        args.prompt_template = None
        print("Ablation Mode: NO PROMPT OPTIMIZATION")
    elif args.ablation_mode == 'baseline':
        args.relevant = False
        args.prompt_template = None
        print("Ablation Mode: BASELINE")
    else:
        print("Ablation Mode: FULL (with dependencies + optimized prompt)")

    target = Path(args.target_path)
    
    # Set ablation-specific output directory
    if args.ablation_output:
        out_dir = Path(args.ablation_output)
    elif args.output_dir:
        out_dir = Path(args.output_dir)
    else:
        if args.ablation_mode != 'full':
            out_dir = target / f"docs_ablation_{args.ablation_mode}"
        else:
            out_dir = target / "docs"

    if args.test_mode:
        test_targets = get_test_targets(str(target))
        if not test_targets:
            print(f"No test targets found in {target}/tests/")
            return
        
        print(f"Test mode: Found {len(test_targets)} targets")
        for name, info in test_targets.items():
            print(f"  - {name}: {info['source']} -> {info['output']}")
        
        # 全项目扫描以获取完整的依赖关系
        analyzer = Analyzer(str(target))
        dot = analyzer.scan()
        if not dot:
            print("Failed to analyze")
            return
        
        file_map = {k: v['path'] for k, v in analyzer.files.items()}
        nav = analyze(dot, str(target), file_map)

        total = 0
        for fname, info in test_targets.items():
            if fname in analyzer.files:
                finfo = analyzer.files[fname]
                # 修改输出路径：使用out_dir而不是原始tests目录
                output_path = out_dir / "tests" / f"{fname}.md"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                count = process_test_file(args, fname, finfo, str(output_path), nav)
                if count:
                    total += count
            else:
                print(f"  [ERROR] {fname} not found in analyzer")
        
        print(f"\nGenerated docs for {total} items in {len(test_targets)} files")
        return

    # 原有的完整模式
    out_dir = Path(args.output_dir) if args.output_dir else target / "docs"

    analyzer = Analyzer(str(target))
    dot = analyzer.scan()

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
