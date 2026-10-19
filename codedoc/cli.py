import os
import ast
import subprocess
import argparse
import time
from pathlib import Path
from threading import Semaphore, Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

from codedoc.config import TEMPLATES, default_template
from codedoc.deps.relations_index import build_index, get_dep
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
            # Guard, not a feature: the prompt should already be section-budgeted
            # (see writer.prompt.clip_source). Warn loudly because truncating here
            # silently drops whatever lands past the cut, including the criteria
            # block or the dependency blocks.
            print(f"  [WARN] prompt {len(msg)} chars exceeds --max_tokens "
                  f"{args.max_tokens}; truncating — required structure may be lost")
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


def _build_tasks(nav, members, source_path):
    """Tasks for one file: (sort_key, dep, display_name, kind, owner).

    Classes are first-class entities now. They were previously reduced to a
    1-2 sentence summary generated from the list of method names, which discarded
    exactly the information the dependency layer was extended to provide
    (inheritance, subclasses, instantiation sites, override obligations).
    """
    # Sort key groups a class with its own methods: (group, class_name, rank, index).
    # With the previous flat keys every class header was emitted before every
    # method, which broke the class -> method hierarchy the artifact must show.
    tasks = []
    for cls_name, cls_info in members.get('classes', {}).items():
        cls_dep = get_dep(nav, cls_name, cls_info.get('key', ''), source_path)
        if cls_dep and cls_dep.get('source_code'):
            tasks.append(((0, cls_name, 0, -1), cls_dep, cls_name, 'class', cls_name))
        for i, method in enumerate(cls_info.get('methods', [])):
            dep = get_dep(nav, method['name'], method['key'], source_path)
            if dep and dep.get('source_code'):
                tasks.append(((0, cls_name, 1, i), dep, method['name'], 'method', cls_name))
    for i, fn in enumerate(members.get('functions', [])):
        dep = get_dep(nav, fn['name'], fn['key'], source_path)
        if dep and dep.get('source_code'):
            tasks.append(((1, '', 0, i), dep, fn['name'], 'function', None))
    return tasks


def _run_tasks(args, tasks):
    """Generate documentation for every task, concurrently."""
    docs = {}
    lock = Lock()

    def worker(task):
        key, dep, name, kind, owner = task
        info = format_dep(dep, args.relevant)
        md = gen_doc(args, dep)
        return key, info, md, name, kind, owner

    with ThreadPoolExecutor(max_workers=10) as ex:
        for fut in as_completed([ex.submit(worker, t) for t in tasks]):
            try:
                key, info, md, name, kind, owner = fut.result()
                with lock:
                    docs[key] = (info, md, name, kind, owner)
            except Exception as exc:
                print(f"  [ERROR] {exc}")
    return docs


def process_file(args, fname, finfo, nav, out_dir, target):
    rel = Path(finfo['path']).relative_to(target)
    info_path = out_dir / rel.with_suffix('.info')
    md_path = out_dir / rel.with_suffix('.md')
    info_path.parent.mkdir(parents=True, exist_ok=True)

    members = finfo['members']
    print(f"\n{fname}.py (classes: {len(members.get('classes', {}))}, "
          f"funcs: {len(members.get('functions', []))})")

    tasks = _build_tasks(nav, members, finfo['path'])
    if not tasks:
        return None

    docs = _run_tasks(args, tasks)

    info_lines = []
    md_lines = [f"# {fname}.py\n\n**Path:** `{finfo['path']}`\n\n---\n\n"]
    stats = {"cls": 0, "func": 0, "method": 0}
    emitted_cls = set()
    has_func_header = False

    for key in sorted(docs.keys()):
        info, md, name, kind, owner = docs[key]
        # The artifact keeps the class -> method hierarchy explicit: a class is a
        # level-2 section and its methods are level-3 sections beneath it, so the
        # generated document mirrors the structure the dependency layer models.
        if kind == 'class':
            stats["cls"] += 1
            emitted_cls.add(name)
            md_lines.append(f"## Class: `{name}`\n\n")
        elif kind == 'method':
            if owner not in emitted_cls:
                emitted_cls.add(owner)
                md_lines.append(f"## Class: `{owner}`\n\n")
            method_name = name.split(".")[-1]
            md_lines.append(f"### Method: `{method_name}`\n\n")
            stats["method"] += 1
        else:
            if not has_func_header:
                md_lines.append("## Functions\n\n")
                has_func_header = True
            md_lines.append(f"### Function: `{name}`\n\n")
            stats["func"] += 1
        info_lines.append(info + "\n" + "=" * 50 + "\n\n")
        if md:
            md_lines.append(md + "\n\n")

    info_path.write_text("".join(info_lines), encoding="utf-8")
    md_path.write_text("".join(md_lines), encoding="utf-8")
    return stats


def process_test_file(args, fname, finfo, output_path, nav):
    """Process a single file and write its documentation to the given path."""
    members = finfo['members']
    print(f"\n{fname}.py (classes: {len(members.get('classes', {}))}, "
          f"funcs: {len(members.get('functions', []))})")

    tasks = _build_tasks(nav, members, finfo['path'])
    if not tasks:
        print(f"  No tasks for {fname}")
        return None

    docs = _run_tasks(args, tasks)
    md_lines = []
    for key in sorted(docs.keys()):
        _info, md, name, kind, owner = docs[key]
        if not md:
            continue
        if kind == 'class':
            md_lines.append(f"## Class: `{name}`\n\n")
        elif kind == 'method':
            md_lines.append(f"### Method: `{name.split('.')[-1]}`\n\n")
        else:
            md_lines.append(f"### Function: `{name}`\n\n")
        md_lines.append(md + "\n\n")
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
    p.add_argument('--max_tokens', type=int, default=16000,
                   help='Hard cap on the assembled prompt, in characters (safety guard). '
                        'Sections should be budgeted before this point.')
    p.add_argument('--source_budget', type=int, default=8000,
                   help='Character budget for the source section of the prompt. Longer '
                        'sources keep their head and tail with an explicit elision marker.')
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

    target = Path(args.target_path).resolve()
    
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
        nav = build_index(str(target))
        if nav is None:
            print("Failed to analyze")
            return

        total = 0
        for fname, info in test_targets.items():
            if fname in nav.files:
                finfo = nav.files[fname]
                # 修改输出路径：使用out_dir而不是原始tests目录
                output_path = out_dir / "tests" / f"{fname}.md"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                count = process_test_file(args, fname, finfo, str(output_path), nav)
                if count:
                    total += count
            else:
                print(f"  [ERROR] {fname} not found in index")
        
        print(f"\nGenerated docs for {total} items in {len(test_targets)} files")
        return

    # 原有的完整模式
    out_dir = Path(args.output_dir) if args.output_dir else target / "docs"

    nav = build_index(str(target))
    if nav is None:
        print("Failed to analyze")
        return

    total = {"cls": 0, "func": 0, "method": 0}
    for fname, finfo in nav.files.items():
        stats = process_file(args, fname, finfo, nav, out_dir, target)
        if stats:
            for k in total:
                total[k] += stats[k]

    print(f"\nOutput: {out_dir}")
    print(f"Classes: {total['cls']}, Methods: {total['method']}, Functions: {total['func']}")


if __name__ == "__main__":
    main()
