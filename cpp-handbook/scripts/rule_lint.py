#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规则号 lint：找出文档/代码注释里写错的 C++ Core Guidelines 规则编号。

为什么需要：规则编号错一位，肉眼几乎看不出来，但会让整段论证失效。
本知识库自建的第一版就有 25 处错引（把并发规则写成 ``Con.5`` 而不是 ``CP.5``、
把所有权规则写成 ``M.5`` 之类），而且**没有任何工具报出来**——是靠逐条比对
328 条标题人工修掉的。把这件事变成脚本，才能保证不再复发。

白名单来自知识库的真源：``knowlege/_meta/core-guidelines-rules.txt``
（由 ``knowlege/_meta/extract-rules.py`` 从 Core Guidelines 原文重建，500 条）。
没有知识库时回退到 skill 自带的 ``references/rule-index.md``（同一份清单的生成副本），
所以本脚本在任何机器上都能跑。

用法：
    python rule_lint.py src include docs
    python rule_lint.py --self          # 只 lint skill 自身
    python rule_lint.py . --ext md,cpp,h
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _kbpath import find_kb_root, kb_root_or_none, relative_to_kb  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
RULE_INDEX_REL = "_meta/core-guidelines-rules.txt"

# 形如 R.11 / ES.31 / Per.1 / CP.20 / CP.con.1 / SL.str.11
TOKEN = re.compile(r"(?<![\w.])([A-Za-z][A-Za-z0-9]{0,5}(?:\.[A-Za-z0-9]+)+)(?![\w.])")
SIMPLE_RULE = re.compile(r"^[A-Z][A-Za-z]*\.\d+$")
DEFAULT_EXTS = {"md", "mdx", "cpp", "cc", "cxx", "h", "hpp", "hh", "txt"}
SKIP_DIRS = {".git", "node_modules"}

# C++ 标准版本号与规则号字面冲突（C.11 / C.20 同时是规则号）。
# 出现在含 "C++" / "标准" / "version" 的行里时按版本理解，降级为提示而非错误。
AMBIGUOUS = {"C.11", "C.14", "C.17", "C.20", "C.23", "C.26"}
VERSION_CONTEXT = re.compile(r"C\+\+|标准|版本|version|std=|gnu\+\+", re.IGNORECASE)

# 这些前缀在 Core Guidelines 里不存在。但它们可能是**别的编号体系**
# （learncpp 用 M.N 表示课时、cppreference 用 "M.N" 标注章节），
# 因此只给提示、不判错——工具没资格断言用户引的是不是 Core Guidelines。
KNOWN_BAD_PREFIX = {"M.", "Mem.", "Cpl.", "SS.", "G."}

# 语义 -> 期望的规则号前缀。白名单只能抓「编号不存在」，
# 抓不到「编号存在但用错章节」（例如并发规则写成 Con.5 而不是 CP.5），靠这张表补上。
#
# 只保留 4 组高置信度映射：更泛的词（类/函数/异常/模板）在这类文档里到处都是，
# 会把整行表格里的多个规则号全部误报。窗口取「编号后紧跟的中文解释」，
# 而不是整行——这样只有当解释本身在说并发/所有权/性能/宏时才提示。
SEMANTIC_HINTS: list[tuple[str, set[str], str]] = [
    (r"并发|线程|数据竞争|多线程|锁|原子", {"CP"},
     "并发规则前缀是 CP.*（CP.con / CP.etc）；Con.* 是 const/不可变默认的旧章节"),
    (r"性能|开销", {"Per"}, "性能规则前缀是 Per.*"),
    (r"宏|预处理", {"ES"}, "宏与语句规则前缀是 ES.*"),
]
# 刻意不收录「所有权」：这词在 F.*（如 F.26 转移所有权）和 CP.*（如 CP.32
# 跨线程共享所有权）的合法规则里都会出现，据此报警会变成纯噪声。
HINT_BEFORE = 18
HINT_AFTER = 20




def load_whitelist(kb: Path) -> dict[str, str]:
    path = kb / RULE_INDEX_REL
    if not path.is_file():
        raise FileNotFoundError(f"规则索引不存在: {path}")
    rules: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ": " not in raw:
            continue
        rid, title = raw.split(": ", 1)
        rules[rid.strip()] = title.strip().strip('"')
    return rules


def load_whitelist_from_index(index_path: Path) -> dict[str, str]:
    """从 skill 自带的 ``references/rule-index.md`` 解析白名单。

    没有知识库时，``references/rule-index.md``（生成物，但已随 skill 分发）
    就是等价的真源副本——它由同一个 ``build_indexes.py`` 从同一份规则清单生成。
    这样 ``rule_lint.py`` 在任何机器上都能用，不强依赖 1GB 的知识库。
    """
    if not index_path.is_file():
        raise FileNotFoundError(f"规则索引不存在: {index_path}")
    rules: dict[str, str] = {}
    for raw in index_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- `([^`]+)`\s*(.*)$", raw)
        if not m:
            continue
        rules[m.group(1).strip()] = m.group(2).strip()
    if not rules:
        raise ValueError(f"规则索引里没解析出任何规则: {index_path}")
    return rules


def resolve_whitelist(kb: Path | None) -> tuple[dict[str, str], str]:
    """返回 (白名单, 来源说明)。优先真源，其次 skill 自带索引副本。"""
    if kb is not None:
        try:
            return load_whitelist(kb), "知识库真源"
        except FileNotFoundError:
            pass
    idx = SKILL_DIR / "references" / "rule-index.md"
    return load_whitelist_from_index(idx), "skill 自带规则索引副本（无知识库）"


def iter_files(paths: list[str], exts: set[str]):
    seen = set()
    for raw in paths:
        p = Path(raw).resolve()
        if not p.exists():
            continue
        files = [p] if p.is_file() else sorted(p.rglob("*"))
        for f in files:
            if not f.is_file():
                continue
            if f.suffix.lower().lstrip(".") not in exts:
                continue
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            key = str(f)
            if key in seen:
                continue
            seen.add(key)
            yield f


def semantic_warn(token: str, line: str, pos: int, line_prefixes: set[str]) -> str | None:
    """规则号前缀与相邻中文解释不符时给出提示（编号存在但用错章节）。

    窗口 = 编号前 HINT_BEFORE 个字符 + 编号后 HINT_AFTER 个字符。
    中文解释既可能在编号前（「并发…见 Con.2」），也可能在编号后（「CP.9（验证并发代码）」）。
    """
    prefix = token.split(".")[0]
    before = line[max(0, pos - HINT_BEFORE): pos]
    after = re.sub(r"^[\s*`：:（(]*", "", line[pos + len(token):])[:HINT_AFTER]
    window = before + " " + after
    for pattern, expected, hint in SEMANTIC_HINTS:
        if not re.search(pattern, window, re.IGNORECASE):
            continue
        if prefix in expected:
            return None
        # 同一行里已经出现了期望前缀的规则号，就不要对其它编号报警
        if line_prefixes & expected:
            return None
        return f"{hint}（当前前缀 {prefix}.*）"
    return None



CG_MARKER = re.compile(r"core\s+guidelines|cppcoreguidelines|核心指南", re.IGNORECASE)
# 文档级判定：只有"在讨论 Core Guidelines"的文档里，未知编号才算硬错误。
# 其它文档里的 M.1 / A.3 / O.1 往往是章节编号（learncpp 用 M.N 表示课时、
# O.N 表示位运算专题、B.N 表示标准更新专题），不能当成错引。
STRICT_VALID_ID_THRESHOLD = 4
# 代码文件里出现 "XX.N" 几乎必然是在引用规则编号，一律按严格模式判定。
CODE_EXTS = {"cpp", "cc", "cxx", "c", "h", "hpp", "hh", "hxx", "ipp", "inl"}


def lint_text(text: str, whitelist: dict[str, str], suffix: str = "") -> tuple[list[dict], list[dict]]:
    errors: list[dict] = []
    warns: list[dict] = []
    known_prefixes = {rid.split(".")[0] for rid in whitelist}

    all_tokens = [m.group(1) for m in TOKEN.finditer(text) if SIMPLE_RULE.match(m.group(1))]
    valid_count = sum(1 for t in all_tokens if t in whitelist)
    strict_doc = (
        suffix.lower().lstrip(".") in CODE_EXTS
        or bool(CG_MARKER.search(text))
        or valid_count >= STRICT_VALID_ID_THRESHOLD
    )

    for lineno, line in enumerate(text.splitlines(), 1):
        if "github.com/isocpp/CppCoreGuidelines" in line:
            continue
        # 本行出现过的所有规则号前缀，供语义检查做"同句已有正确前缀"的豁免判断
        line_prefixes = {m.group(1).split(".")[0]
                         for m in TOKEN.finditer(line)
                         if SIMPLE_RULE.match(m.group(1))}
        for m in TOKEN.finditer(line):
            tok = m.group(1)
            if not SIMPLE_RULE.match(tok):
                continue
            if tok in whitelist:
                if tok in AMBIGUOUS and VERSION_CONTEXT.search(line):
                    warns.append({"line": lineno, "token": tok,
                                  "msg": "版本号与规则号字面冲突（已按版本理解）"})
                else:
                    hint = semantic_warn(tok, line, m.start(), line_prefixes)
                    if hint:
                        warns.append({"line": lineno, "token": tok, "msg": hint})
                continue
            prefix = tok.split(".")[0]
            if prefix in KNOWN_BAD_PREFIX:
                warns.append({"line": lineno, "token": tok,
                               "msg": f"前缀 {prefix} 不是 Core Guidelines 规则号"
                                      "（若指并发规则，应为 CP.*；若指其它编号体系可忽略）"})
            elif prefix in known_prefixes:
                if strict_doc:
                    errors.append({"line": lineno, "token": tok,
                                   "msg": "编号不存在（该前缀有效，但这个编号没有）"})
                else:
                    warns.append({"line": lineno, "token": tok,
                                  "msg": "编号不在索引中；本文档未在讨论 Core Guidelines，"
                                         "可能属于其它编号体系"})
            else:
                warns.append({"line": lineno, "token": tok,
                              "msg": "前缀未知，可能是笔误的规则号"})
    return errors, warns




def main() -> int:
    ap = argparse.ArgumentParser(description="C++ Core Guidelines 规则号 lint")
    ap.add_argument("paths", nargs="*", default=["."], help="要扫描的文件或目录")
    ap.add_argument("--ext", default="md,cpp,cc,cxx,h,hpp,hh,txt", help="扩展名，逗号分隔")
    ap.add_argument("--self", action="store_true", help="扫描 skill 自身目录")
    ap.add_argument("--quiet", action="store_true", help="只输出错误")
    args = ap.parse_args()

    paths = [str(SKILL_DIR)] if args.self else (args.paths or ["."])
    exts = {e.strip().lower().lstrip(".") for e in args.ext.split(",") if e.strip()}

    kb = kb_root_or_none()
    try:
        whitelist, source = resolve_whitelist(kb)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    total_err = 0
    total_warn = 0
    scanned = 0
    for f in iter_files(paths, exts):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        errors, warns = lint_text(text, whitelist, suffix=f.suffix)
        if not errors and not warns:
            continue
        rel = relative_to_kb(f, kb) if kb is not None else str(f)
        for e in errors:
            total_err += 1
            print(f"ERROR {rel}:{e['line']}  规则号 {e['token']}  {e['msg']}")
        if not args.quiet:
            for w in warns:
                total_warn += 1
                print(f"WARN  {rel}:{w['line']}  {w['token']}  {w['msg']}")

    print("-" * 72)
    print(f"白名单规则数: {len(whitelist)}（来源: {source}）   扫描文件: {scanned}   "
          f"错误: {total_err}   提示: {total_warn}")
    return 1 if total_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
