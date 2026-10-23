#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检索评测：中文提问能不能把对应的知识页召回来？

本脑 `embedding_disabled: true` → `gbrain search` 走的是纯 FTS 关键词匹配
（没有向量语义召回）。本脚本用一批真实提问量出两件事：
  1. 期望页面的排名 / 是否进 top-N
  2. 谁在抢第一——是我们写的精炼主题页，还是上游大文档

用法：python _meta/retrieval-eval.py
"""
import json
import os
import re
import subprocess

ROOT = r"F:\soft\00selfmade\skill-c++\knowlege"
SOURCE = "cpp-knowledge"

# (提问, 期望命中的页面 slug, 提问类型)
CASES = [
    ("所有权",            "topics/ownership-and-lifetime", "宽泛"),
    ("RAII 资源管理",     "topics/ownership-and-lifetime", "宽泛"),
    ("移动语义",          "topics/move-semantics",         "宽泛"),
    ("完美转发",          "topics/move-semantics",         "精确"),
    ("std::forward",      "topics/move-semantics",         "精确"),
    ("noexcept 移动构造",  "topics/move-semantics",         "精确"),
    ("迭代器失效",        "topics/stl-containers-algorithms", "精确"),
    ("erase remove",      "topics/stl-containers-algorithms", "精确"),
    (" Concepts 约束",     "topics/templates-and-concepts",  "精确"),
    ("悬垂引用",          "topics/pitfalls-and-antipatterns", "精确"),
    ("shared_ptr 循环引用", "topics/pitfalls-and-antipatterns", "精确"),
    ("data race",         "topics/concurrency",             "精确"),
    ("内存序 memory_order", "topics/concurrency",            "精确"),
    ("ASan 内存错误",     "topics/toolchain-and-debugging",  "精确"),
    ("基准测试 benchmark", "topics/performance",            "精确"),
    ("CMake 最佳实践",     "topics/project-practices",       "精确"),
    ("std::expected",     "topics/error-handling",          "精确"),
    ("C++23 新特性",       "topics/modern-cpp-features",     "精确"),
]

LINE = re.compile(r"^\[([0-9.]+)\]\s+(\S+)\s+--\s*(.*)$")


def search(q):
    try:
        p = subprocess.run(["gbrain", "search", q, "--source", SOURCE],
                           capture_output=True, text=True, timeout=300,
                           encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return []
    hits = []
    for ln in (p.stdout or "").splitlines():
        m = LINE.match(ln.strip())
        if m:
            hits.append((float(m.group(1)), m.group(2), m.group(3)[:48]))
    return hits


def main():
    print("=" * 78)
    print("检索评测  —  source: cpp-knowledge  (embedding 关闭 → 纯 FTS 关键词)")
    print("=" * 78)
    print(f"{'提问':<22}{'类型':<6}{'期望页排名':<12}{'top1 是谁':<32}")
    print("-" * 78)

    rows = []
    for q, want, kind in CASES:
        hits = search(q)
        slugs = [s for _, s, _ in hits]
        rank = slugs.index(want) + 1 if want in slugs else None
        top1 = slugs[0] if slugs else "(无结果)"
        rows.append((q, kind, want, rank, top1, len(hits)))
        print(f"{q:<22}{kind:<6}{str(rank or '未召回'):<12}{top1[:30]:<32}")

    print("-" * 78)
    exact = [r for r in rows if r[1] == "精确"]
    broad = [r for r in rows if r[1] == "宽泛"]
    for label, group in (("精确提问", exact), ("宽泛提问", broad)):
        if not group:
            continue
        hit1 = sum(1 for r in group if r[3] == 1)
        hit3 = sum(1 for r in group if r[3] and r[3] <= 3)
        hit10 = sum(1 for r in group if r[3] and r[3] <= 10)
        miss = sum(1 for r in group if not r[3])
        print(f"{label}: top1={hit1}/{len(group)}  top3={hit3}/{len(group)}  "
              f"top10={hit10}/{len(group)}  未召回={miss}/{len(group)}")
    allhit = sum(1 for r in rows if r[3])
    print(f"合计: 期望页被召回 {allhit}/{len(rows)}")

    out = os.path.join(ROOT, "_meta", "retrieval-eval.md")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 检索评测结果\n\n")
        f.write(f"source: `{SOURCE}`（embedding 关闭 → 纯 FTS 关键词匹配）\n\n")
        f.write("| 提问 | 类型 | 期望页面 | 排名 | top1 命中 |\n")
        f.write("|---|---|---|---|---|\n")
        for q, kind, want, rank, top1, n in rows:
            f.write(f"| {q} | {kind} | `{want}` | {rank or '未召回'} | `{top1}` |\n")
    print("written:", out)


if __name__ == "__main__":
    main()
