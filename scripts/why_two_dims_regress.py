"""Why do Completeness and Conciseness not improve with the rest?

Reads the judged ISO documents of both systems and reports, per dimension:
  * the score distribution
  * how document length relates to the score
  * the judge's own reasons for the low scores, as recurring phrases

Used to answer the question with evidence rather than conjecture.
"""
from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(r"E:\Pycharm_projects\CodeEval")
TEN = ["dify_api", "fairseq", "flask-main", "joblib", "numpy", "openui", "pyro", "ragflow", "sonnet", "torch"]
DIMS = ("Completeness", "Conciseness", "Comprehensibility", "Metadata")


def doc_root(system: str, repo: str) -> Path:
    if system == "ours":
        return REPO / "outputs/matrix_v6/iso_26514" / repo
    return REPO / "outputs/baselines/repoagent" / repo


def doc_text(system: str, repo: str, name: str) -> str:
    path = doc_root(system, repo) / name
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def score_files(system: str, repo: str):
    if system == "ours":
        d = REPO / "outputs/matrix_v6/iso_26514" / repo / "scores_iso_26514"
    else:
        d = REPO / "outputs/baselines/repoagent" / repo / "scores_iso_26514"
    return sorted(d.glob("*.json")) if d.exists() else []


def collect(system: str):
    rows = []
    for repo in TEN:
        for f in score_files(system, repo):
            payload = json.loads(f.read_text(encoding="utf-8"))
            verdict = payload.get("verdict") or {}
            name = payload.get("document") or ""
            text = doc_text(system, repo, name)
            row = {"repo": repo, "qname": payload.get("qname", ""), "doc": name,
                   "chars": len(text), "words": len(text.split())}
            for dim in DIMS:
                entry = verdict.get(dim) or {}
                row[dim] = entry.get("judge")
                row[dim + "_why"] = entry.get("evidence") or ""
            rows.append(row)
    return rows


def dist(rows, dim):
    vals = [r[dim] for r in rows if isinstance(r[dim], (int, float))]
    if not vals:
        return None
    hist = Counter(int(v) for v in vals)
    return {"n": len(vals), "mean": statistics.mean(vals), "median": statistics.median(vals),
            "hist": dict(sorted(hist.items()))}


def correlate(rows, dim):
    pairs = [(r["words"], r[dim]) for r in rows if isinstance(r[dim], (int, float))]
    if len(pairs) < 10:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else None


def reasons(rows, dim, threshold=3):
    text = " ".join(r[dim + "_why"].lower() for r in rows if isinstance(r[dim], (int, float)) and r[dim] <= threshold)
    pats = {
        "repetition": r"repetit|duplicat|redundan|repeat",
        "verbosity": r"verbose|wordy|too long|overly long|excessive detail|prolix",
        "boilerplate/empty sections": r"boilerplate|empty|placeholder|no content|nothing to report|\bnone\b",
        "missing content": r"miss|lack|omit|absent|incomplete|does not (describe|mention|cover)|no mention|silent on",
        "vague": r"vague|generic|superficial|shallow|imprecise|ambiguous",
        "hard to read": r"hard to read|unclear|confusing|difficult to follow|poorly",
        "structured": r"well[- ]organi|clear(ly)? structur|section|bullet",
    }
    return {k: len(re.findall(v, text)) for k, v in pats.items()}


def main():
    ours = collect("ours")
    base = collect("repoagent")
    print(f"  \ours 文档 {len(ours)} 篇 | RepoAgent 文档 {len(base)} 篇\n")

    print("=== 长度 ===")
    for name, rows in (("CodeDoc", ours), ("RepoAgent", base)):
        w = [r["words"] for r in rows]
        print(f"  {name:<10} 中位词数 {statistics.median(w):.0f}  均值 {statistics.mean(w):.0f}  "
              f"范围 {min(w)}–{max(w)}")

    print("\n=== 分数分布 ===")
    for dim in DIMS:
        do, db = dist(ours, dim), dist(base, dim)
        print(f"  {dim}:")
        for name, d in (("CodeDoc", do), ("RepoAgent", db)):
            if d:
                print(f"    {name:<10} n={d['n']:<4} 均值 {d['mean']:.2f} 中位 {d['median']:.1f} 分布 {d['hist']}")

    print("\n=== 长度与分数的相关（Pearson, 词数 vs 分数）===")
    for dim in ("Completeness", "Conciseness"):
        co, cb = correlate(ours, dim), correlate(base, dim)
        fmt = lambda v: "n/a" if v is None else f"{v:+.3f}"
        print(f"  {dim}: CodeDoc {fmt(co)} | RepoAgent {fmt(cb)}")

    print("\n=== 判官在低分(≤3)时的用词频次 ===")
    for dim in ("Completeness", "Conciseness"):
        print(f"  {dim}:")
        print(f"    CodeDoc   {reasons(ours, dim)}")
        print(f"    RepoAgent {reasons(base, dim)}")

    # 同一实体两侧分数的配对比较，看是普遍回落还是少数实体拖累
    print("\n=== 同一实体配对（ISO, 单轮）===")
    index = {}
    for r in ours:
        index[(r["repo"], r["qname"])] = r
    for dim in ("Completeness", "Conciseness"):
        worse = better = same = 0
        gaps = []
        for r in base:
            o = index.get((r["repo"], r["qname"]))
            if not o or not isinstance(o[dim], (int, float)) or not isinstance(r[dim], (int, float)):
                continue
            d = o[dim] - r[dim]
            gaps.append(d)
            if d < 0:
                worse += 1
            elif d > 0:
                better += 1
            else:
                same += 1
        if gaps:
            print(f"  {dim}: 我们更低 {worse} / 更高 {better} / 相同 {same}，平均差 {statistics.mean(gaps):+.3f}")

    print("\n=== 低分样例（CodeDoc, Conciseness ≤3）===")
    shown = 0
    for r in ours:
        if isinstance(r["Conciseness"], (int, float)) and r["Conciseness"] <= 3 and shown < 3:
            print(f"  [{r['repo']} {r['qname']}] {r['words']} 词, 分数 {r['Conciseness']}")
            print(f"    判官: {r['Conciseness_why'][:300]}")
            shown += 1


if __name__ == "__main__":
    main()
