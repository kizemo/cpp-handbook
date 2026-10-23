#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把工程根路径从 F:\\soft\\00selfmade\\skill-c++ 改成 F:\\soft\\00selfmade\\cpp-handbook。

先改文本并提交，再动目录——顺序反过来的话，目录一旦改名，权限门禁可能
失去工作区锚点，后续就写不进去了。
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"F:\soft\00selfmade\skill-c++")
OLD = r"F:\soft\00selfmade\skill-c++"
NEW = r"F:\soft\00selfmade\cpp-handbook"

TARGETS = [
    "knowledge-tools/check-links.py",
    "knowledge-tools/retrieval-eval.py",
    "docs/book-to-skill/chapters-plan.md",
    "docs/book-to-skill/check_chapters.py",
    "docs/skill-forge/measure-tokens.py",
    "docs/book-to-skill/README.md",
    "knowledge-tools/README.md",
    ".b2s/count_tokens.py",
    ".b2s/check_chapters.py",
    ".b2s/chapters-plan.md",
]

total = 0
for rel in TARGETS:
    p = ROOT / rel
    if not p.is_file():
        print(f"  skip  {rel}（不存在）")
        continue
    t = p.read_text(encoding="utf-8")
    n = t.count(OLD)
    if n == 0:
        print(f"  skip  {rel}（无匹配）")
        continue
    p.write_text(t.replace(OLD, NEW), encoding="utf-8", newline="\n")
    total += n
    print(f"  edit  {rel}  x{n}")

print(f"\n共替换 {total} 处")

print("\n=== 复查：仓库内是否还有旧工程路径 ===")
hits = []
for p in ROOT.rglob("*"):
    if not p.is_file() or ".git" in p.parts or "knowlege" in p.parts or "archive" in p.parts:
        continue
    if p.suffix.lower() not in {".md", ".py", ".ps1", ".yaml", ".yml", ".jsonl", ".txt", ".tsv"}:
        continue
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        continue
    if OLD in t:
        hits.append(str(p.relative_to(ROOT)))
for h in hits:
    print("  STILL: " + h)
print("  (无 STILL 行 = 已清零)")
