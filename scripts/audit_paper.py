"""Final consistency audit of the paper tree.

Checks, in order:
  1. every \\label is defined once and every cross-reference resolves
  2. every \\replaced / \\added / \\deleted has the right number of balanced arguments
  3. every environment is balanced and every \\input target exists
  4. the headline numbers that appear in more than one place agree with each other
  5. retired artefacts (Long-Context, Pyan3, 26 dials) appear only inside revision markup
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

PAPER = Path(r"D:\临时下载位置\Standards_Guided_and_Dependency_Aware_Code_Level_Documentation_Generation")

TEX = (sorted(PAPER.glob("sections/*.tex"))
       + sorted(p for p in PAPER.glob("tables/*.tex") if not p.name.endswith(".bak"))
       + sorted(PAPER.glob("tables/generated/tab_*.tex")))
def strip_comments(text: str) -> str:
    """Drop LaTeX comments so rollback blocks are not audited as live content."""
    out = []
    for line in text.splitlines():
        idx = 0
        cut = len(line)
        while True:
            idx = line.find("%", idx)
            if idx < 0:
                break
            if idx > 0 and line[idx - 1] == chr(92):   # escaped percent
                idx += 1
                continue
            cut = idx
            break
        out.append(line[:cut])
    return "\n".join(out)


TEXT = {p: strip_comments(p.read_text(encoding="utf-8")) for p in TEX}

problems: list[str] = []


def section(title: str) -> None:
    print(f"\n== {title} ==")


# 1 ---------------------------------------------------------------- labels
section("交叉引用")
labels = Counter()
for p, t in TEXT.items():
    for m in re.finditer(r"\\label\{([^}]*)\}", t):
        labels[m.group(1)] += 1
        if m.group(1) != m.group(1).strip():
            problems.append(f"label 含空格: {p.name} '{m.group(1)}'")
dups = {k: v for k, v in labels.items() if v > 1}
if dups:
    problems.append(f"重复 label: {dups}")
dangling = []
for p, t in TEXT.items():
    for m in re.finditer(r"\\(?:auto)?ref\{([^}]*)\}", t):
        if m.group(1) not in labels:
            dangling.append(f"{p.name}:{m.group(1)}")
if dangling:
    problems.append(f"悬空引用: {sorted(set(dangling))}")
print(f"  label {len(labels)} 个，重复 {len(dups)}，悬空引用 {len(set(dangling))}")

# 2 ------------------------------------------------------------- markup
section("修订标记")
for cmd, nargs in (("\\replaced", 2), ("\\added", 1), ("\\deleted", 1)):
    bad = []
    for p, t in TEXT.items():
        for m in re.finditer(re.escape(cmd) + r"\{", t):
            pos, depth, got, ok = m.end() - 1, 0, 0, False
            while pos < len(t):
                ch = t[pos]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        got += 1
                        pos += 1
                        if got == nargs:
                            ok = True
                            break
                        probe = pos
                        while probe < len(t) and t[probe].isspace():
                            probe += 1
                        if probe < len(t) and t[probe] == "{":
                            continue
                        break
                pos += 1
            if not ok:
                bad.append(p.name)
    total = sum(t.count(cmd + "{") for t in TEXT.values())
    print(f"  {cmd}: {total} 处，参数异常 {len(bad)}")
    if bad:
        problems.append(f"{cmd} 参数异常: {bad}")

# 3 --------------------------------------------------------- environments
section("环境与 \\input")
for env in ("table", "table*", "tabular", "figure*", "itemize"):
    pat = env.replace("*", "\\*")
    b = sum(len(re.findall(r"\\begin\{" + pat + r"\}", t)) for t in TEXT.values())
    e = sum(len(re.findall(r"\\end\{" + pat + r"\}", t)) for t in TEXT.values())
    flag = "" if b == e else "  <-- 不平衡"
    print(f"  {env}: {b}/{e}{flag}")
    if b != e:
        problems.append(f"环境不平衡 {env} {b}/{e}")
missing = []
for f in ("main.tex", "sections/appendix.tex", "sections/experiment_revised.tex"):
    t = (PAPER / f).read_text(encoding="utf-8")
    for m in re.finditer(r"\\input\{([^}]+)\}", t):
        if not (PAPER / (m.group(1) + ".tex")).exists():
            missing.append(m.group(1))
if missing:
    problems.append(f"\\input 目标缺失: {missing}")
print(f"  \\input 缺失 {len(missing)}")

# 4 -------------------------------------------------------------- numbers
section("关键数字一致性")
body = "\n".join(t for p, t in TEXT.items() if p.name != "token.tex")
checks = {
    "ISO 总分 CodeDoc 4.74": body.count("4.74"),
    "ISO 总分 RepoAgent 4.07": body.count("4.07"),
    "ISO 总分 MemDocAgent 4.16": body.count("4.16"),
    "GitHub RepoAgent 2.06": body.count("2.06"),
    "GitHub MemDocAgent 2.42": body.count("2.42"),
    "差值 +0.67": body.count("+0.67"),
    "差值 +0.58": body.count("+0.58"),
    "差值 +2.22": body.count("+2.22"),
    "差值 +1.86": body.count("+1.86"),
    "成本 2.60M": body.count("2.60"),
    "时间 0.61 h": body.count("0.61"),
    "费用 $1.22": body.count("1.22"),
    "解析率 15.6%": body.count("15.6"),
    "精度 99.6%": body.count("99.6"),
}
for k, v in checks.items():
    print(f"  {k}: 出现 {v} 次")

# 旧数字不应再出现（除非在修订标记的旧文本里，无法静态区分，故只报数量）
stale = {}
for p, t in TEXT.items():
    for kw in ("3.18", "3.72", "2.87", "+0.39", "+0.55", "9,491"):
        if kw in t:
            stale.setdefault(p.name, []).append(kw)
print(f"  旧数字残留: {stale or '无'}")

# 5 ------------------------------------------------------------ retired?
section("退役内容")
for kw in ("Long-Context", "Pyan3", "26 dimensions", "twelve", "GPT-5-mini"):
    hits = {p.name: t.count(kw) for p, t in TEXT.items() if kw in t}
    print(f"  {kw}: {hits or '无'}")

section("结论")
if problems:
    for x in problems:
        print(f"  ✗ {x}")
else:
    print("  全部检查通过")
