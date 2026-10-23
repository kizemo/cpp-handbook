#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从知识库真源生成 skill 的索引层（references/*.md）。

这是防「第二份真相源」的核心机制：
- ``references/rule-index.md``  = 真源规则索引（497 条）的**生成副本**
- ``references/source-map.md``  = 来源路由表（规则写在脚本里，路径逐个现场验证）

生成物禁止手改：改了就会被 ``verify_bundle.py`` 判为陈旧。
新增/修改知识库后跑：

    python build_indexes.py            # 重建
    python build_indexes.py --check    # 只比对，不一致时退出码 1
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from _kbpath import find_kb_root  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent
REF_DIR = SKILL_DIR / "references"
RULE_INDEX_REL = "_meta/core-guidelines-rules.txt"

PREFIX_DOC = {
    "P": "原则（Principles）",
    "A": "适配器（Adapters）",
    "R": "资源（Resources）",
    "S": "源文件（Source files）",
    "SF": "源文件（Source files, 文件级）",
    "C": "类（Classes）",
    "F": "函数（Functions）",
    "E": "错误处理（Error handling）",
    "Con": "并发（Concurrency，旧章节）",
    "CP": "并发（Concurrency，CP.con / CP.etc）",
    "ES": "表达式与语句（Expressions and statements）",
    "Per": "性能（Performance）",
    "T": "模板（Templates）",
    "CPL": "C 与 C++ 的接口（Interop）",
    "SL": "标准库（Standard library）",
}

# 问题类型 -> (查哪里, 补充说明)。路径相对知识库根，生成时逐个验证存在性。
ROUTES: list[tuple[str, str, str]] = [
    ("某条规则的原文到底怎么说", "01-core-guidelines/CppCoreGuidelines.md",
     "按规则号 grep；中文全译见 02-core-guidelines-zh/CppCoreGuidelines-zh-CN.md"),
    ("所有权 / 生命周期 / 智能指针", "topics/ownership-and-lifetime.md",
     "R.11 / R.20 / R.21 / R.24，Rule of Zero/Five"),
    ("移动语义 / 完美转发 / noexcept", "topics/move-semantics.md", "std::move / std::forward"),
    ("模板与 Concepts", "topics/templates-and-concepts.md", "C++20 concepts 与约束写法"),
    ("STL 容器 / 算法 / 迭代器失效", "topics/stl-containers-algorithms.md",
     "含 std::remove 误用、erase-remove 惯用法"),
    ("并发 / 数据竞争 / 内存序", "topics/concurrency.md", "对应 Core Guidelines 的 CP.* 规则"),
    ("错误处理 / 异常安全", "topics/error-handling.md", "E.* 规则与异常安全三保证"),
    ("性能优化", "topics/performance.md", "Per.* 规则与可测量的优化"),
    ("C++11/14/17/20/23 特性速查", "06-modern-cpp-features/",
     "每个版本一个文件，外加 modern-cpp-features-cheatsheet.md"),
    ("陷阱与反模式 / UB 清单", "topics/pitfalls-and-antipatterns.md", "17 类高频坑"),
    ("CMake / CI / 测试工程", "topics/project-practices.md", "搭一个可交付的 C++ 工程"),
    ("CMake 最佳实践（可直接抄的模板）", "13-cmake-best-practices/",
     "含 CMakePresets、工具链、依赖管理"),
    ("编译 / 调试 / Sanitizer", "topics/toolchain-and-debugging.md", "ASan / UBSan / TSan 用法"),
    ("Google C++ 风格指南", "09-google-style/cppguide.md",
     "HTML 转 Markdown；中文版在 10-google-style-zh/"),
    ("标准库 API 语义（权威）", "18-cppreference-doc/headers-md/",
     "按头文件分篇，如 memory.md / vector.md / algorithm.md"),
    ("ISO 标准草案原文", "12-iso-draft/markdown/", "39 篇按标准章节拆分"),
    ("算法实现 + 单元测试", "07-algorithms/", "按算法分类的目录树"),
    ("算法题解（C++）", "08-leetcode-cases/", "0001-1000.md 等分段题解"),
    ("中文系统教程", "19-learncpp-cn/", "learncpp.com 中文全译"),
    ("中文面试知识点 / 短文", "20-cpp-notes-cn/", "智能指针.md 等 11 篇短文"),
    ("真实工程示例（实时系统）", "11-real-time-cpp/", "书稿 + 配套工程"),
    ("现代 C++ 工程脚手架", "14-modern-cpp-starter/", "clang-format / CMake 模板"),
]


def read_rules(kb: Path) -> list[tuple[str, str]]:
    path = kb / RULE_INDEX_REL
    if not path.is_file():
        raise FileNotFoundError(f"规则索引不存在: {path}")
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ": " not in raw:
            continue
        rid, title = raw.split(": ", 1)
        out.append((rid.strip(), title.strip().strip('"')))
    return out


def render_rule_index(rules: list[tuple[str, str]]) -> str:
    groups: dict[str, list[tuple[str, str]]] = {}
    for rid, title in rules:
        groups.setdefault(rid.split(".")[0], []).append((rid, title))

    lines = [
        "# Core Guidelines 规则索引（生成物，勿手改）",
        "",
        "> 由 `build_indexes.py` 从知识库真源生成。",
        "> 真源原文：`knowlege/01-core-guidelines/CppCoreGuidelines.md`；",
        "> 抽取结果：`knowlege/_meta/core-guidelines-rules.txt`。",
        f"> 共 {len(rules)} 条规则，{len(groups)} 个分组。",
        "",
        "> 用途：核对规则号是否存在、查看原文标题。",
        "> 查某条规则在原文里的上下文，用 `kb_lookup.py` 或直接 grep 原文。",
        "",
    ]
    for prefix in sorted(groups, key=lambda p: (p != "P", p)):
        doc = PREFIX_DOC.get(prefix, "")
        items = groups[prefix]
        lines.append(f"## {prefix}.* — {doc}（{len(items)} 条）")
        lines.append("")
        for rid, title in items:
            lines.append(f"- `{rid}` {title}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_source_map(kb: Path) -> str:
    lines = [
        "# 来源路由表（生成物，勿手改）",
        "",
        "> 由 `build_indexes.py` 生成：路由规则写在脚本里，**路径逐个现场验证**。",
        "> 知识库目录变动后重跑生成器即可，不会出现指向已删除文件的死链。",
        "",
        "## 按问题类型查",
        "",
        "| 我要查 | 位置 | 说明 |",
        "|---|---|---|",
    ]
    for question, target, note in ROUTES:
        p = kb / target
        mark = "✅" if p.exists() else "❌ 缺失"
        shown = target.rstrip("/") + ("/" if p.is_dir() else "")
        lines.append(f"| {question} | `{shown}` {mark} | {note} |")

    lines += [
        "",
        "## 三层知识结构的分工",
        "",
        "| 层 | 目录 | 用途 |",
        "|---|---|---|",
        "| 原文层 | `01-` ~ `20-` | 上游仓库原文，一字不改；含中文主题页 `topics/` 与索引页 `index/` |",
        "| 主题层 | `topics/` | 中文原创消化层，11 篇，结构为「结论 → 规则 → 案例 → 坑 → 出处」 |",
        "| 索引层 | `index/` | 来源台账、学习路线、案例索引、知识地图 |",
        "",
        "## 总入口",
        "",
        "- 知识地图：`index/knowledge-map.md`",
        "- 来源台账（作者 / 许可 / star / commit）：`index/sources.md`",
        "- 学习路线：`index/learning-path.md`",
        "- 案例索引：`index/cases.md`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 skill 索引层")
    ap.add_argument("--check", action="store_true", help="只比对，不写文件")
    args = ap.parse_args()

    try:
        kb = find_kb_root()
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    rules = read_rules(kb)
    outputs = {
        REF_DIR / "rule-index.md": render_rule_index(rules),
        REF_DIR / "source-map.md": render_source_map(kb),
    }

    REF_DIR.mkdir(parents=True, exist_ok=True)
    stale = []
    for path, content in outputs.items():
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == content:
            print(f"OK   {path.name}")
            continue
        stale.append(path.name)
        if args.check:
            print(f"STALE {path.name}")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
            print(f"生成 {path.name}  ({len(content)} chars)")

    if args.check:
        if stale:
            print("索引层与真源不一致，请运行: python build_indexes.py")
            return 1
        print("索引层与真源一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
