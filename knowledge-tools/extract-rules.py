#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Core Guidelines 原文重建规则索引（真源 -> 索引，单向、可重复）。

原索引 core-guidelines-rules.txt 只有 328 条，且**整章缺失 CP.*（并发）**，
来源是手写抽取。规则标题在原文里的格式固定为：

    ### <a name="anchor"></a>RULE.ID: Title

本脚本直接按该格式重建，输出 `ID: "Title"` 每行一条，去重后按 ID 排序。
被跳过的行（无 title、非规则格式）会统计上报，便于发现格式漂移。

用法：
    python extract-rules.py            # 重建 core-guidelines-rules.txt
    python extract-rules.py --check    # 只比对，不写文件；不一致时退出码 1
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KB_ROOT = HERE.parent
SOURCE = KB_ROOT / "01-core-guidelines" / "CppCoreGuidelines.md"
INDEX = HERE / "core-guidelines-rules.txt"

# 规则标题行：### <a name="xxx"></a>ID: Title
# 上游会给个别规则加 `?` 后缀（表示该规则有争议 / 待定），例如
# `### <a name="rt-var"></a>T.142?: Use template variables to simplify notation`
HEADING = re.compile(r"^###\s*<a\s+name=\"[^\"]*\"\s*></a>\s*([A-Za-z][A-Za-z0-9]*"
                      r"(?:\.[A-Za-z0-9]+)+)(\?)?\s*:\s*(.+?)\s*$")
# 目录条目：* [T.30: Use concept negation (...)](#rt-???)
# 上游有少量规则只存在于目录（正文标题缺失，锚点字面写作 "???"），
# 例如 T.30 / T.31。只抽标题会漏掉它们，因此目录也扫一遍作为补充。
# 但目录里还混着**章节名**（C.con / CP.con / GSL.owner / Pro.type …），
# 那不是规则号，用「末段必须是数字」把它们排除。
TOC_ENTRY = re.compile(r"^\s*\*\s*\[([A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)*\.\d+)\s*:\s*"
                        r"([^\]]+?)\]\(#")
# 规则 ID：字母段 + 点分段，例如 R.11 / ES.31 / Per.1 / CP.con.1 / SL.str.11
RULE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)+$")


def parse_source(text: str) -> tuple[dict[str, str], int, int]:
    """返回 (规则号 -> 标题, 跳过的标题行数, 只在目录中出现的规则数)。"""
    rules: dict[str, str] = {}
    skipped = 0
    for line in text.splitlines():
        if not line.startswith("### "):
            continue
        m = HEADING.match(line)
        if not m:
            skipped += 1
            continue
        rid, disputed, title = m.group(1), m.group(2), m.group(3)
        if not RULE_ID.match(rid):
            skipped += 1
            continue
        if disputed:
            title = f"{title} [upstream marks this rule with '?']"
        # 同一规则号可能重复出现（例如目录与正文），保留首个非空标题
        if rid not in rules and title:
            rules[rid] = title
    toc_only = 0
    for line in text.splitlines():
        m = TOC_ENTRY.match(line)
        if not m:
            continue
        rid, title = m.group(1), m.group(2).strip()
        if rid in rules or not RULE_ID.match(rid) or not title:
            continue
        rules[rid] = title
        toc_only += 1
    return rules, skipped, toc_only


def read_existing(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        if ": " not in raw:
            continue
        rid, title = raw.split(": ", 1)
        out[rid.strip()] = title.strip().strip('"')
    return out


def render(rules: dict[str, str]) -> str:
    def sort_key(rid: str) -> tuple:
        # 头段按字母排序，后续段统一成 (类型标记, 值) 以便数字段按数值排序，
        # 避免 R.10 排在 R.9 前面；类型标记保证 int 与 str 之间也可比较。
        parts = rid.split(".")
        head = parts[0]
        tail = tuple((0, int(p)) if p.isdigit() else (1, p) for p in parts[1:])
        return (head, tail)

    return "".join(f"{rid}: \"{rules[rid]}\"\n" for rid in sorted(rules, key=sort_key))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只比对，不写文件")
    args = ap.parse_args()

    if not SOURCE.exists():
        print(f"[error] 原文不存在: {SOURCE}", file=sys.stderr)
        return 2

    text = SOURCE.read_text(encoding="utf-8")
    rules, skipped, toc_only = parse_source(text)
    existing = read_existing(INDEX)
    new_text = render(rules)

    added = sorted(set(rules) - set(existing))
    removed = sorted(set(existing) - set(rules))
    changed = sorted(rid for rid in set(rules) & set(existing)
                     if rules[rid] != existing[rid])

    print(f"原文规则数: {len(rules)}   旧索引规则数: {len(existing)}   "
          f"跳过标题行: {skipped}   仅见于目录: {toc_only}")
    print(f"新增: {len(added)}   缺失: {len(removed)}   标题变化: {len(changed)}")
    for rid in added[:40]:
        print(f"  + {rid}: {rules[rid][:70]}")
    if len(added) > 40:
        print(f"  ... 另有 {len(added) - 40} 条")

    if args.check:
        same = INDEX.exists() and INDEX.read_text(encoding="utf-8") == new_text
        print("CHECK:", "一致" if same else "不一致（需要重建）")
        return 0 if same else 1

    INDEX.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"已写入: {INDEX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
