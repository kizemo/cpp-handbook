#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""章节路由回归评测：用 SKILL.md 章节索引表里的触发词，检验 references/routing-eval.jsonl 里的每条提问能否路由到期望章节。

评测对象是「路由」而不是「回答质量」：一条提问如果连字面触发词都命中不了期望章节，
说明 SKILL.md 的索引缺词（用户按字面提问时读不到该章）；如果期望章节能命中但被别人压过，
说明触发词有歧义（同一批词把用户导去了别的章）。

解析规则（对应 SKILL.md 的章节索引表）：
    | 章 | 标题 | 触发词（命中任一即读该章） |
    |---|---|---|
    | [ch01](chapters/xxx.md) | 所有权与生命周期 | shared_ptr, 循环引用, 悬垂 |

    - 第 3 列按 ',' 切分再 strip()，得到该章的触发词列表；
    - 第 2 列（标题）归一化后作为该章的一个额外可命中词；
    - 匹配前把 query 和触发词都去掉所有空白再比较（'现代 C++' 能命中 '现代C++'）；
    - 英文统一 lower()，中文不做转换。

打分与判定：
    一个触发词出现即该章 +1 分；得分最高的章节 = 预测章节；并列最高取章号最小者。
    预测章节 == expect            -> PASS
    expect 得分 > 0 但不是最高分    -> FAIL（歧义/排序错），列出所有得分 >= 预测分数的章节
    expect 得分 == 0              -> FAIL（索引缺词）

用法：
    cd <skill 目录>
    python scripts\\route_eval.py                              # 评测默认 skill 目录（脚本所在目录的上一级）
    python scripts\\route_eval.py --skill D:\\path\\cpp-handbook    # 指定 skill 目录（跑安装后的副本）
    python scripts\\route_eval.py --eval my-eval.jsonl          # 指定评测集（默认 references/routing-eval.jsonl）
    python scripts\\route_eval.py --verbose                     # 额外打印每个章节命中的触发词

退出码：0 = 全部 PASS，1 = 有失败，2 = 输入缺失或格式错误。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 章节索引行：| [ch01](chapters/xxx.md) | 标题 | 触发词, 触发词, ... |
ROW_RE = re.compile(r"^\|\s*\[(ch\d{2})\]\(([^)]+)\)\s*\|([^|]*)\|([^|]*)\|")
WS_RE = re.compile(r"\s+")

EVAL_REL = Path("references") / "routing-eval.jsonl"


def normalize(text: str) -> str:
    """归一化：去掉所有空白字符并统一小写。

    这样 '现代 C++'、'现代C++'、'现代  C++' 视为同一个词；
    'std::move' 也能命中 'std::move ' 这类带空格的写法。
    """
    return WS_RE.sub("", text).lower()


def parse_index(skill_md: Path) -> dict:
    """从 SKILL.md 的章节索引表解析出 {chNN: {"title":..., "triggers":[...]}}。

    容错：表头行与分隔行不含 [chNN](...)，正则自然匹配不到，直接跳过。
    """
    text = skill_md.read_text(encoding="utf-8")
    chapters: dict = {}
    for raw in text.splitlines():
        m = ROW_RE.match(raw.strip())
        if not m:
            continue
        cid, _path, title, trigger_cell = m.groups()
        triggers = [t.strip() for t in trigger_cell.split(",") if t.strip()]
        title = title.strip()
        # 标题是第 2 列，作为该章的一个额外可命中词（已存在则不重复计分）
        if title and not any(normalize(t) == normalize(title) for t in triggers):
            triggers.append(title)
        chapters[cid] = {"title": title, "triggers": triggers}
    return chapters


def load_eval(path: Path) -> list:
    """读 JSONL 评测集，每行一个 {id, query, expect, note}。"""
    cases = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno} 不是合法 JSON：{exc}") from exc
            for key in ("id", "query", "expect"):
                if key not in obj:
                    raise ValueError(f"{path}:{lineno} 缺少字段 {key!r}")
            cases.append(obj)
    return cases


def match_query(query: str, chapters: dict) -> dict:
    """字面包含匹配（去空白 + 小写）。返回 {chNN: [命中的触发词]}。"""
    q = normalize(query)
    hits: dict = {}
    for cid, info in chapters.items():
        matched = [t for t in info["triggers"] if normalize(t) and normalize(t) in q]
        if matched:
            hits[cid] = matched
    return hits


def predict(hits: dict) -> tuple:
    """预测章节：得分最高者胜；并列最高取章号最小者。

    返回 (预测章节, 并列最高分的章节列表)。
    """
    if not hits:
        return None, []
    best = max(len(v) for v in hits.values())
    tied = sorted(c for c, v in hits.items() if len(v) == best)
    return tied[0], tied


def format_scores(hits: dict) -> str:
    return ", ".join(f"{c}({len(v)})" for c, v in sorted(hits.items()))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="章节路由回归评测（零依赖，仅标准库）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    parser.add_argument(
        "--skill", type=Path, default=None,
        help="skill 目录（含 SKILL.md 与 references/），默认取脚本所在目录的上一级")
    parser.add_argument(
        "--eval", type=Path, default=None,
        help="评测集 JSONL 路径，默认 <skill>/references/routing-eval.jsonl")
    parser.add_argument(
        "--verbose", action="store_true",
        help="额外打印每个章节命中的触发词")
    args = parser.parse_args()

    skill_dir = (args.skill if args.skill else Path(__file__).resolve().parent.parent).resolve()
    skill_md = skill_dir / "SKILL.md"
    eval_path = (args.eval if args.eval else skill_dir / EVAL_REL).resolve()

    if not skill_md.is_file():
        print(f"找不到 SKILL.md：{skill_md}", file=sys.stderr)
        return 2
    if not eval_path.is_file():
        print(f"找不到评测集：{eval_path}", file=sys.stderr)
        return 2

    try:
        chapters = parse_index(skill_md)
        cases = load_eval(eval_path)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"读取失败：{exc}", file=sys.stderr)
        return 2

    if not chapters:
        print(f"SKILL.md 里没有解析到任何章节索引行：{skill_md}", file=sys.stderr)
        return 2

    empty = sorted(c for c, i in chapters.items() if not i["triggers"])
    if empty:
        print(f"警告：这些章节没有触发词（索引列可能没填）：{', '.join(empty)}", file=sys.stderr)

    print(f"skill 目录：{skill_dir}")
    print(f"章节数：{len(chapters)}   评测条数：{len(cases)}")
    print("-" * 72)

    passed = 0
    ambiguous = 0
    missing = 0
    failed = 0

    for case in cases:
        cid = str(case["id"])
        query = str(case["query"])
        expect = str(case["expect"])
        hits = match_query(query, chapters)
        pred, tied = predict(hits)
        pred_score = len(hits.get(pred, [])) if pred else 0

        if pred == expect:
            passed += 1
            print(f"PASS {cid}  {query}  预测={pred} 期望={expect}")
            if args.verbose:
                for c in sorted(hits):
                    print(f"      {c}({len(hits[c])}): {', '.join(hits[c])}")
            continue

        failed += 1
        print(f"FAIL {cid}  {query}  预测={pred or '无'} 期望={expect}")
        if expect not in hits:
            missing += 1
            print(f"      索引缺词：{expect} 的触发词一个都没命中（其它章节命中：{format_scores(hits) or '无'}）")
        else:
            ambiguous += 1
            rivals = sorted(c for c, v in hits.items() if len(v) >= pred_score)
            print(f"      歧义/排序错：期望章命中 {len(hits[expect])} 个，预测章 {pred} 命中 {pred_score} 个")
            print(f"      得分 >= 预测分数的章节：{', '.join(rivals)}")
            if len(tied) > 1:
                print(f"      并列歧义：{', '.join(tied)}")
        if args.verbose:
            for c in sorted(hits):
                print(f"      {c}({len(hits[c])}): {', '.join(hits[c])}")

    print("-" * 72)
    print(f"通过 {passed} 条，失败 {failed} 条（其中歧义 {ambiguous} 条、缺词 {missing} 条）")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
