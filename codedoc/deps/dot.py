import os
import ast
import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Node:
    id: str
    label: str
    group: str
    file: str = ""
    cls: str = None


@dataclass
class DepInfo:
    name: str
    display_name: str
    path: str
    code: str
    used_by: list = field(default_factory=list)
    uses: list = field(default_factory=list)


class DotParser:
    def __init__(self, folder_name=None):
        self.group_map = {}
        self.nodes = {}
        self.edges = {}
        self.folder_name = folder_name  # 用于去掉文件夹前缀

    def _normalize_nid(self, nid):
        """去掉节点ID中的文件夹前缀"""
        if self.folder_name and nid.startswith(self.folder_name + "__"):
            nid = nid[len(self.folder_name) + 2:]
        return nid

    def parse(self, content):
        self._parse_nodes(content)
        self._infer_classes()
        self._parse_edges(content)

    def _normalize_nid(self, nid):
        """去掉节点ID中的文件夹前缀"""
        if self.folder_name and nid.startswith(self.folder_name + "__"):
            nid = nid[len(self.folder_name) + 2:]
        return nid

    def _parse_nodes(self, content):
        pattern = r'(\w+) \[label="([^"]*)"[^]]*group="(\d+)"\];'
        for m in re.finditer(pattern, content):
            nid, label, group = m.groups()
            nid = self._normalize_nid(nid)
            if "__" not in nid:
                self.group_map[group] = nid
        for m in re.finditer(pattern, content):
            nid, label, group = m.groups()
            nid = self._normalize_nid(nid)
            self.nodes[nid] = Node(nid, label, group, self.group_map.get(group, ""))

    def _infer_classes(self):
        for nid, node in self.nodes.items():
            if "__" not in nid:
                continue
            parts = nid.split("__")
            if len(parts) >= 3:
                node.cls = parts[1]

    def _parse_edges(self, content):
        for src, tgt in re.findall(r'(\w+(?:__\w+)*)\s*->\s*(\w+(?:__\w+)*)', content):
            src = self._normalize_nid(src)
            tgt = self._normalize_nid(tgt)
            self.edges.setdefault(src, []).append(tgt)

    def get(self, nid):
        return self.nodes.get(nid)

    def callers(self, nid):
        return [s for s, ts in self.edges.items() if nid in ts]

    def callees(self, nid):
        return self.edges.get(nid, [])


class CodeFinder:
    def __init__(self, base="."):
        self.base = Path(base)
        self.cache = {}

    def set_base(self, path):
        self.base = Path(path)

    def set_cache(self, file_map):
        self.cache = {k: Path(v) for k, v in file_map.items()}

    def build_cache(self):
        self.cache = {f.stem: f for f in self.base.rglob("*.py")}

    def find(self, node):
        f = self.cache.get(node.file)
        if not f or not f.exists():
            return None
        try:
            src = f.read_text(encoding='utf-8')
            tree = ast.parse(src)
            if node.cls:
                r = self._find_method(tree, node.cls, node.label, f)
                if r:
                    return r
                r = self._find_nested(tree, node.cls, node.label, f)
                if r:
                    return r
            r = self._find_func(tree, node.label, f)
            return r or self._find_class(tree, node.label, f)
        except SyntaxError:
            return None

    def _find_method(self, tree, cls, method, f):
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef) and n.name == cls:
                for item in n.body:
                    if isinstance(item, ast.FunctionDef) and item.name == method:
                        return self._extract(item, f)
        return None

    def _find_nested(self, tree, outer, inner, f):
        for n in ast.iter_child_nodes(tree):
            if isinstance(n, ast.FunctionDef) and n.name == outer:
                for item in ast.walk(n):
                    if isinstance(item, ast.FunctionDef) and item.name == inner:
                        return self._extract(item, f)
        return None

    def _find_func(self, tree, name, f):
        for n in ast.iter_child_nodes(tree):
            if isinstance(n, ast.FunctionDef) and n.name == name:
                return self._extract(n, f)
        return None

    def _find_class(self, tree, name, f):
        for n in ast.iter_child_nodes(tree):
            if isinstance(n, ast.ClassDef) and n.name == name:
                return self._extract(n, f)
        return None

    def _extract(self, node, f):
        lines = f.read_text(encoding='utf-8').splitlines(keepends=True)
        return ''.join(lines[node.lineno - 1:getattr(node, 'end_lineno', node.lineno + 10)])


class Navigator:
    def __init__(self, root):
        self.root = Path(root)
        self.folder_name = Path(root).name  # 获取文件夹名
        self.parser = DotParser(self.folder_name)
        self.finder = CodeFinder(root)

    def build(self, dot, file_map=None):
        self.parser.parse(dot)
        if file_map:
            self.finder.set_cache(file_map)
        else:
            self.finder.build_cache()

    def get_dep(self, nid, fpath):
        node = self.parser.get(nid)
        if not node:
            return None
        self.finder.set_base(str(Path(fpath).parent))
        code = self.finder.find(node)
        name = f"{node.cls}.{node.label}" if node.cls else node.label
        info = DepInfo(nid, name, fpath, code)
        for cid in self.parser.callers(nid):
            self._add_dep(cid, info.used_by)
        for cid in self.parser.callees(nid):
            self._add_dep(cid, info.uses)
        return info

    def _add_dep(self, nid, lst):
        node = self.parser.get(nid)
        if not node:
            return
        code = self.finder.find(node)
        if not code:
            return
        name = f"{node.cls}.{node.label}" if node.cls else node.label
        lst.append({name: code})

    def has(self, nid):
        return nid in self.parser.nodes


def analyze(dot, root, file_map=None):
    nav = Navigator(root)
    nav.build(dot, file_map)
    return nav


def get_dep(nav, display, nid, fpath):
    if not nav.has(nid):
        return None
    info = nav.get_dep(nid, fpath)
    if not info or not info.code:
        return None
    return {
        "name": info.name,
        "real_name": info.display_name,
        "path": info.path,
        "source_code": info.code,
        "used_by": info.used_by,
        "uses": info.uses
    }


def _build_section(items, title):
    if not items:
        return ""
    lines = [f"## {title}\n"]
    for item in items:
        for name, code in item.items():
            lines.append(f"### {name}\n```python\n{code}\n```\n")
    return ''.join(lines)


def format_dep(info, include_deps):
    uses = _build_section(info['uses'], "Uses") if include_deps else ""
    used_by = _build_section(info['used_by'], "Used by") if include_deps else ""
    return f"""# {info["real_name"]}
## Path
`{info["path"]}`

## Definition
```python
{info["source_code"]}
```

{uses}
{used_by}
"""


def build_prompt(info, args):
    uses = _build_section(info['uses'], "Dependencies") if args.relevant else ""
    used_by = _build_section(info['used_by'], "Dependents") if args.relevant else ""
    
    # Simple prompt for ablation study (no template)
    if args.prompt_template is None:
        simple_prompt = f"""Generate documentation for the following code in {args.language}.

Code to document:
```python
{info["source_code"]}
```
uses:
{uses}

used_by:
{used_by}

Provide clear and concise documentation."""
        return simple_prompt
    
    # Use template file
    try:
        with open(args.prompt_template, 'r', encoding='utf-8') as f:
            tpl = f.read()
    except FileNotFoundError:
        tpl = "Generate docs for {real_name}\n\n{source_code}\n\n{uses}\n{used_by}"
    return tpl.format(
        real_name=info["real_name"],
        path=info["path"],
        source_code=info["source_code"],
        uses=uses,
        used_by=used_by,
        language=args.language
    )
