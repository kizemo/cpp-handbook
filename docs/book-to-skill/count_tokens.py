#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 tiktoken 精确计量 skill 各部分的 token 数。

book-to-skill 的硬约束是「SKILL.md 正文 < 4000 tokens，章节文件按需加载」。
本脚本给出实测值，而不是估算。
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILL = Path(__file__).resolve().parent.parent / "cpp-handbook"
try:
    import tiktoken
except ImportError:
    print("tiktoken 未安装：pip install tiktoken")
    raise SystemExit(2)

enc = tiktoken.get_encoding("cl100k_base")
o200k = tiktoken.get_encoding("o200k_base")


def count(text: str) -> tuple[int, int]:
    return len(enc.encode(text)), len(o200k.encode(text))


print(f"{'文件':46s} {'字符':>7s} {'cl100k':>8s} {'o200k':>7s}")
print("-" * 74)

parts = [SKILL / "SKILL.md", SKILL / "glossary.md", SKILL / "patterns.md",
         SKILL / "cheatsheet.md"]
parts += sorted((SKILL / "chapters").glob("ch*.md"))
parts += sorted((SKILL / "references").glob("*.md"))

tot_c = tot_o = 0
core_c = core_o = 0
for p in parts:
    if not p.is_file():
        continue
    t = p.read_text(encoding="utf-8")
    c, o = count(t)
    tot_c += c
    tot_o += o
    if p.parent.name == "chapters" or p.name in ("SKILL.md", "glossary.md",
                                                  "patterns.md", "cheatsheet.md"):
        core_c += c
        core_o += o
    rel = p.relative_to(SKILL).as_posix()
    print(f"{rel:46s} {len(t):7d} {c:8d} {o:7d}")

print("-" * 74)
print(f"{'合计（全部文件）':46s} {'':7s} {tot_c:8d} {tot_o:7d}")
print(f"{'核心层（SKILL + 3 支撑 + 15 章）':46s} {'':7s} {core_c:8d} {core_o:7d}")

sk = (SKILL / "SKILL.md").read_text(encoding="utf-8")
c, o = count(sk)
print()
print(f"SKILL.md 硬约束：< 4000 tokens  ->  cl100k {c} / o200k {o}  "
      f"{'OK' if c < 4000 else '超限'}")
