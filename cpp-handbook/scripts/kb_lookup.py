#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地全文检索知识库（不依赖 GBrain 脑锁）。

为什么不用 GBrain：本机脑是单写锁模型，任何查询都可能因被别的 serve 独占而报
``pglite_busy``；而 skill 必须在任何时候都能查。知识库是 git 仓库里的静态文件，
本地 grep 足够快，也不占用共享资源。

语义：默认要求**所有**查询词都命中（AND），若没有任何文件满足全部词，
自动降级为「命中任意词」（OR）并标注 ``部分命中``。这比纯 AND 友好，
比纯 OR 精确——检索评测里多词组合的 AND 语义曾导致整体落空。

用法：
    python kb_lookup.py "所有权 shared_ptr"
    python kb_lookup.py "std::remove erase" --top 8
    python kb_lookup.py "静态初始化" --ext md --path topics
    python kb_lookup.py "virtual destructor" --json
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _kbpath import find_kb_root, relative_to_kb  # noqa: E402

DEFAULT_EXTS = {"md", "mdx"}
SKIP_DIR_NAMES = {".git", "node_modules", "_meta"}
MAX_FILE_BYTES = 4 * 1024 * 1024
SNIPPET_WIDTH = 200


def tokenize(query: str) -> list[str]:
    """按空白切词；保留 C++ 标识符中的点与下划线。"""
    raw = [t for t in re.split(r"\s+", query.strip()) if t]
    return [t.strip("\"'`(),;:") for t in raw if t.strip("\"'`(),;:")]


def iter_files(kb: Path, exts: set[str], subpath: str | None):
    base = kb
    if subpath:
        base = (kb / subpath).resolve()
        if not base.exists():
            return
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower().lstrip(".") not in exts:
            continue
        if any(part in SKIP_DIR_NAMES for part in p.parts):
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield p


def read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def search(kb: Path, tokens: list[str], exts: set[str], subpath: str | None,
           top: int) -> list[dict]:
    hits: list[dict] = []
    for p in iter_files(kb, exts, subpath):
        text = read_text(p)
        if text is None:
            continue
        low = text.lower()
        matched = [t for t in tokens if t.lower() in low]
        # 文件名也参与匹配：主题页正文是中文，文件名是英文 kebab-case，
        # 英文查询词（ownership / concurrency）只能靠文件名命中中文主题页。
        stem = p.stem.lower()
        stem_flat = stem.replace("-", " ").replace("_", " ")
        name_hits = [t for t in tokens
                     if t.lower() in stem or t.lower() in stem_flat]
        matched_all = matched + [t for t in name_hits if t not in matched]
        if not matched_all:
            continue

        lines = text.splitlines()
        # 每个查询词只按"最好的一次命中"计分，额外出现只给递减的加分。
        # 否则 864KB 的 Core Guidelines 原文会因为重复出现几十次 "shared_ptr"
        # 而把专门讲这个问题的 8KB 主题页压下去。
        score = 0.0
        first_lines = []
        for t in matched:
            best = 0.0
            best_line = None
            extra = 0
            for idx, line in enumerate(lines):
                ll = line.lower()
                if t.lower() not in ll:
                    continue
                extra += 1
                weight = 1.0 + 1.0 / (1.0 + idx / 40.0)
                if line.lstrip().startswith("#"):
                    weight += 1.5
                if weight > best:
                    best = weight
                    best_line = (idx + 1, line.strip())
                if extra >= 8:
                    break
            score += best + 0.4 * min(extra - 1, 5)
            if best_line and best_line not in first_lines and len(first_lines) < 3:
                first_lines.append(best_line)
        for t in name_hits:
            score += 8.0  # 文件名命中权重：足以让英文词找到中文主题页

        hits.append({
            "file": relative_to_kb(p, kb),
            "score": round(score, 2),
            "matched": matched_all,
            "total_tokens": len(tokens),
            "complete": len(matched_all) == len(tokens),
            "hits": first_lines,
        })

    # 按相关度排序。不用「完整命中优先」——那会把得分最高的文件挤下去：
    # 中文主题页正文没有英文词 "cycle"，只能部分命中，但讲的就是这件事。
    hits.sort(key=lambda h: (-h["score"], h["file"]))
    for h in hits:
        h["partial"] = not h["complete"]
    return hits[:top]


def render(results: list[dict], tokens: list[str], kb: Path) -> None:
    if not results:
        print("无命中。换用英文原词再试一次，或查 knowlege/index/sources.md 找来源目录。")
        print("（注意：检索无命中不等于该主题不存在。）")
        return
    n_full = sum(1 for r in results if not r["partial"])
    print(f"查询: {' '.join(tokens)}   命中 {len(results)} 个文件   "
          f"（完整命中 {n_full}，部分命中 {len(results) - n_full}）")
    print("-" * 72)
    for i, r in enumerate(results, 1):
        flag = "" if not r["partial"] else "  [部分命中]"
        print(f"{i}. {r['file']}   score={r['score']}{flag}")
        for ln, snippet in r["hits"][:2]:
            snippet = snippet[:SNIPPET_WIDTH]
            print(f"     L{ln}: {snippet}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description="本地检索 C++ 知识库")
    ap.add_argument("query", nargs="+", help="查询词（支持中英文，多个词按 AND 优先）")
    ap.add_argument("--top", type=int, default=6, help="返回条数（默认 6）")
    ap.add_argument("--ext", default="md", help="扩展名，逗号分隔（默认 md）")
    ap.add_argument("--path", default=None, help="限定子目录（相对知识库根）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    exts = {e.strip().lower().lstrip(".") for e in args.ext.split(",") if e.strip()}
    tokens = tokenize(" ".join(args.query))
    if not tokens:
        print("查询为空。", file=sys.stderr)
        return 2

    try:
        kb = find_kb_root()
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    results = search(kb, tokens, exts, args.path, args.top)
    if args.json:
        print(json.dumps({"kb": str(kb), "tokens": tokens, "results": results},
                         ensure_ascii=False, indent=2))
    else:
        render(results, tokens, kb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
