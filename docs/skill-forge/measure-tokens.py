#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""改前 / 改后 token 实测对比。

改前的 SKILL.md 全量数据来自上一轮 book-to-skill 的实测记录（cl100k 3932 /
o200k 3322），本脚本复算 description 这一个能单独复现的部分，并对改后的
文件做全量实测。
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True

import tiktoken

ROOT = Path(r"F:\soft\00selfmade\cpp-handbook")
SKILL = ROOT / "cpp-handbook"
enc = tiktoken.get_encoding("cl100k_base")
o200k = tiktoken.get_encoding("o200k_base")


def c(t):
    return len(enc.encode(t)), len(o200k.encode(t))


old_desc = (ROOT / "docs" / "skill-forge" / "baseline-description-v2.0.txt").read_text(encoding="utf-8").strip()
new_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
new_desc = new_text.split("---")[1]
new_desc = new_desc.split("description:", 1)[1].split("\nargument-hint")[0].strip()

print("=" * 74)
print("索引层（description）：每个会话都付，与是否触发无关")
print("-" * 74)
oc, oo = c(old_desc)
nc, no = c(new_desc)
print(f"  改前  {len(old_desc):4d} chars  cl100k {oc:5d}  o200k {oo:5d}  ({len(old_desc.split())} 词)")
print(f"  改后  {len(new_desc):4d} chars  cl100k {nc:5d}  o200k {no:5d}  ({len(new_desc.split())} 词)")
print(f"  节省  {oc - nc:5d} tokens (cl100k, {(1 - nc / oc) * 100:.0f}%)   "
      f"o200k {oo - no} ({(1 - no / oo) * 100:.0f}%)")

print()
print("=" * 74)
print("加载层（SKILL.md 全量）：每次触发都付")
print("-" * 74)
nc2, no2 = c(new_text)
print(f"  改前  10588 chars  cl100k  3932  o200k  3322")
print(f"  改后  {len(new_text):5d} chars  cl100k {nc2:5d}  o200k {no2:5d}")
print(f"  节省  {3932 - nc2:5d} tokens (cl100k, {(1 - nc2 / 3932) * 100:.0f}%)   "
      f"o200k {3322 - no2} ({(1 - no2 / 3322) * 100:.0f}%)")
print(f"  行数  改前 193 行  ->  改后 {len(new_text.splitlines())} 行")

print()
print("=" * 74)
print("运行层（按需加载，不常驻）")
print("-" * 74)
cf = (SKILL / "references" / "core-framework.md").read_text(encoding="utf-8")
fc, fo = c(cf)
print(f"  references/core-framework.md  {len(cf)} chars  cl100k {fc}  o200k {fo}")
print("  ↑ 改前这些内容在 SKILL.md 里常驻；改后只有问「整体该怎么写」才加载。")

print()
print("=" * 74)
print("渐进式披露三档合计")
print("-" * 74)
print(f"  改前  索引 {oc} + 加载 3932              = 常驻 {oc + 3932} tokens")
print(f"  改后  索引 {nc} + 加载 {nc2}              = 常驻 {nc + nc2} tokens"
      f"   ({(1 - (nc + nc2) / (oc + 3932)) * 100:.0f}% ↓)")
print(f"  改后  再加 L1（问整体方案时）             = {nc + nc2 + fc} tokens")
print(f"        但具体问题只需 1 章：ch05 = {c((SKILL / 'chapters' / 'ch05-concurrency.md').read_text(encoding='utf-8'))[0]} tokens")
