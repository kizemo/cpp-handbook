#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wiki 双链完整性检查。

检查两类边：
  1. wiki 链接   [[topics/xxx]]            —— GBrain 的 wikilink
  2. markdown 相对链接 [出处](../xx/a.md)    —— GBrain 的 markdown link

判定：
  - 断链：目标文件不存在
  - 单向边：A→B 但 B 没有回指 A（只在 wiki 链接之间判定互反；
            markdown 边指向上游原文，上游不会回指我们）

用法：python _meta/check-links.py
"""
import os
import re
import sys
from collections import defaultdict

ROOT = r"F:\soft\00selfmade\cpp-handbook\knowlege"
LINK = re.compile(r"\[\[([^\]|#]+?)(?:\|[^\]]*)?\]\]")
MDLINK = re.compile(r"\[[^\]]+\]\(([^)#]+\.md)(?:#[^)]*)?\)")
FENCE = re.compile(r"(?ms)^```.*?^```")
INLINE = re.compile(r"`[^`\n]*`")

IGNORE_DIRS = {"_meta"}
GRAPH_DIRS = ["topics", "index"]


def slug_of(rel_path: str) -> str:
    """GBrain 的 slug 规则：相对路径去掉 .md，小写折叠。"""
    s = rel_path.replace("\\", "/")
    if s.lower().endswith(".md"):
        s = s[:-3]
    return s.lower()


def strip_code(text: str) -> str:
    """去掉围栏代码块与行内代码——人眼看到的是代码，不是链接。

    GBrain 自己的解析器不区分代码区，但本页不存在的目标会被直接跳过
    （resolveSlugAll 返回空 → continue），所以最终行为一致：都不产生边。
    """
    text = FENCE.sub("", text)
    return INLINE.sub("", text)


def collect():
    """返回 (pages, wiki_edges, md_edges, broken_md)"""
    pages = {}                       # slug -> (rel_path, wiki_targets)
    wiki_edges = defaultdict(set)    # src -> {dst}  仅 wiki 链接
    md_edges = defaultdict(set)      # src -> {dst}  仅 markdown 相对链接
    broken_md = []

    for d in GRAPH_DIRS:
        base = os.path.join(ROOT, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in IGNORE_DIRS]
            for fn in sorted(filenames):
                if not fn.lower().endswith(".md"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT)
                with open(full, "rb") as f:
                    text = f.read().decode("utf-8", errors="replace")
                stripped = strip_code(text)
                src = slug_of(rel)

                wiki_targets = set()
                for m in LINK.finditer(stripped):
                    t = m.group(1).strip()
                    if t:
                        wiki_targets.add(t)

                for m in MDLINK.finditer(stripped):
                    t = m.group(1).strip()
                    if "://" in t:
                        continue
                    resolved_path = os.path.normpath(
                        os.path.join(os.path.dirname(full), t)).replace("\\", "/")
                    rel_resolved = os.path.relpath(resolved_path, ROOT).replace("\\", "/")
                    if os.path.exists(os.path.join(ROOT, rel_resolved)):
                        md_edges[src].add(slug_of(rel_resolved))
                    else:
                        broken_md.append((rel, t, rel_resolved))

                pages[src] = (rel, wiki_targets)
    return pages, wiki_edges, md_edges, broken_md


def main():
    pages, wiki_edges, md_edges, broken_md = collect()
    if not pages:
        print("no pages found")
        return 1

    known = set(pages.keys())
    broken_wiki = []
    for src, (rel, targets) in pages.items():
        for t in sorted(targets):
            cand = slug_of(t)
            if cand in known:
                wiki_edges[src].add(cand)
            elif os.path.exists(os.path.join(ROOT, t + ".md")):
                wiki_edges[src].add(cand)
            else:
                broken_wiki.append((rel, t))

    # 互反检查只在 wiki 链接之间做
    oneway = []
    for src, dsts in wiki_edges.items():
        for d in dsts:
            if d in wiki_edges and src not in wiki_edges[d]:
                oneway.append((src, d))

    all_dst = set()
    for v in list(wiki_edges.values()) + list(md_edges.values()):
        all_dst |= v
    orphans = sorted(known - all_dst)

    print("=" * 70)
    print("WIKI LINK INTEGRITY CHECK")
    print("=" * 70)
    print(f"nodes (authored pages)      : {len(pages)}")
    print(f"wiki edges                  : {sum(len(v) for v in wiki_edges.values())}")
    print(f"markdown edges to upstream  : {sum(len(v) for v in md_edges.values())}")
    print(f"broken wiki links           : {len(broken_wiki)}")
    print(f"broken markdown links       : {len(broken_md)}")
    print(f"one-way wiki edges          : {len(oneway)}")
    print(f"orphan nodes                : {len(orphans)}")

    if broken_wiki:
        print("\n--- broken wiki links ---")
        for rel, t in sorted(broken_wiki):
            print(f"  {rel}  ->  [[{t}]]")
    if broken_md:
        print("\n--- broken markdown links ---")
        for rel, t, r in sorted(broken_md):
            print(f"  {rel}  ->  {t}   (resolved: {r})")
    if oneway:
        print("\n--- one-way wiki edges (missing back-link) ---")
        for s, d in sorted(oneway):
            print(f"  {s}  ->  {d}    (missing {d} -> {s})")
    if orphans:
        print("\n--- nodes without any outgoing edge ---")
        for o in orphans:
            print(f"  {o}")

    print("\n--- out-degree (wiki / markdown) ---")
    for s in sorted(pages):
        print(f"  {s:45s} {len(wiki_edges.get(s, ())):3d} / {len(md_edges.get(s, ())):3d}")

    ok = not broken_wiki and not broken_md and not oneway and not orphans
    print("\nRESULT:", "PASS - links intact, graph fully reciprocal"
          if ok else "FAIL - see the sections above")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
