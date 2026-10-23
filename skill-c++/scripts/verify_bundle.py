#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill 与知识库的一致性校验（防陈旧的唯一防线）。

检查项：
1.  必需文件齐不齐
2.  SKILL.md frontmatter 合规（含 skill-forge 原则：路由触发词 / triggers / 版本号）
3.  索引层与真源一致（**需要知识库**；缺知识库时降级为 SKIP）
4.  文档中引用的路径存在
5.  文档中引用的规则编号在真源白名单内
6.  scripts/*.py 存在且语法正确
7.  章节齐不齐、结构对不对
8.  SKILL.md 章节索引链到真实文件
9.  无构建产物残留（.pyc / __pycache__）
10. 渐进式披露结构成立（L0 够瘦、四层都有落点）
11. frontmatter 符合 skill-forge 书写原则
12. 章节索引路由回归通过（scripts/route_eval.py）

**知识库可选**：本 skill 可以脱离知识库独立工作（章节、规则索引、速查表都在
skill 里）。没有知识库时，只有第 3 项降级为 SKIP——它校验的是生成物与真源的
一致性，需要真源才能判。其它项全部照跑。

用法：
    python verify_bundle.py
退出码 0 表示无失败项（SKIP 不算失败），1 表示有失败项。
"""
from __future__ import annotations

import py_compile
import re
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from _kbpath import find_kb_root  # noqa: E402
from rule_lint import lint_text, load_whitelist  # noqa: E402
import build_indexes  # noqa: E402

REQUIRED_FILES = [
    "SKILL.md",
    "build_indexes.py",
    "glossary.md",
    "patterns.md",
    "cheatsheet.md",
    "references/checklists.md",
    "references/core-framework.md",
    "references/rule-index.md",
    "references/source-map.md",
    "scripts/_kbpath.py",
    "scripts/kb_lookup.py",
    "scripts/rule_lint.py",
    "scripts/verify_bundle.py",
    "scripts/selftest.py",
    "agents/openai.yaml",
]

# book-to-skill 形态：15 个章节文件，ch01..ch15
CHAPTER_COUNT = 15
CHAPTER_REQUIRED_SECTIONS = [
    "## Core Idea",
    "## Frameworks Introduced",
    "## Key Concepts",
    "## Mental Models",
    "## Anti-patterns",
    "## Key Takeaways",
    "## Connects To",
]

# 只校验反引号里的行内代码，且必须是「像路径」的片段
PATH_TOKEN = re.compile(r"^[A-Za-z0-9_.\-/]+(?:/[A-Za-z0-9_.\-/]+)+/?$")
RULE_ID_HEAD = re.compile(r"^[A-Z][A-Za-z]*\.\d+$")

# 渐进式披露：L0（SKILL.md）的行数上限。超过就说明该下沉的内容没下沉。
L0_MAX_LINES = 150

ok_count = 0
fail_count = 0
skip_count = 0


def ok(msg: str) -> None:
    global ok_count
    ok_count += 1
    print(f"  PASS  {msg}")


def fail(msg: str) -> None:
    global fail_count
    fail_count += 1
    print(f"  FAIL  {msg}")


def skip(msg: str) -> None:
    """降级项：环境不具备导致无法判定，不算失败，但必须显式报出来。"""
    global skip_count
    skip_count += 1
    print(f"  SKIP  {msg}")


def check_required_files() -> None:
    print("[1] 必需文件")
    for rel in REQUIRED_FILES:
        p = SKILL_DIR / rel
        if p.is_file() and p.stat().st_size > 0:
            ok(rel)
        else:
            fail(f"缺失或为空: {rel}")


def check_frontmatter() -> None:
    print("[2] SKILL.md frontmatter")
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---"):
        fail("SKILL.md 未以 frontmatter 开头")
        return
    end = text.find("\n---", 3)
    if end == -1:
        fail("frontmatter 未闭合")
        return
    fm = text[3:end]
    for key in ("name:", "description:"):
        if re.search(rf"^{re.escape(key)}", fm, re.MULTILINE):
            ok(f"frontmatter 含 {key}")
        else:
            fail(f"frontmatter 缺 {key}")
    m = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
    if m and m.group(1) == SKILL_DIR.name:
        ok(f"name 与目录名一致: {m.group(1)}")
    elif m:
        fail(f"name({m.group(1)}) 与目录名({SKILL_DIR.name}) 不一致")
    if m and not re.match(r"^[a-z0-9][a-z0-9-]*$", m.group(1)):
        # Agent Skills 规范只允许小写字母/数字/连字符。MiniMax Code 本身接受
        # 其它字符（实测可按名加载），但跨宿主发布会被拒。
        print(f"  WARN  name({m.group(1)}) 不符合 Agent Skills 命名规范"
              "（只允许小写字母/数字/连字符）——跨宿主发布前请用 "
              "install.ps1 -SkillName <合规名> 重装")


def check_generated(kb) -> None:
    print("[3] 索引层与真源一致")
    if kb is None:
        skip("未找到知识库根目录，无法比对生成物与真源（SKIP 不算失败）")
        return
    try:
        rules = build_indexes.read_rules(kb)
    except FileNotFoundError as exc:
        fail(str(exc))
        return
    expected = {
        SKILL_DIR / "references" / "rule-index.md": build_indexes.render_rule_index(rules),
        SKILL_DIR / "references" / "source-map.md": build_indexes.render_source_map(kb),
    }
    for path, content in expected.items():
        if not path.is_file():
            fail(f"未生成: {path.name}（运行 build_indexes.py）")
            continue
        if path.read_text(encoding="utf-8") == content:
            ok(f"{path.name} 与真源一致")
        else:
            fail(f"{path.name} 已陈旧（运行 build_indexes.py）")


def check_paths(kb) -> None:
    print("[4] 文档中引用的路径")
    roots = [SKILL_DIR]
    if kb is not None:
        roots += [kb, kb.parent]
    checked = 0
    missing = []
    kb_scoped = 0
    for rel in ["SKILL.md", "references/checklists.md", "references/source-map.md",
                "references/core-framework.md"]:
        p = SKILL_DIR / rel
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            for cand in inline_code_spans(line):
                if not cand or " " in cand:
                    continue
                if cand.startswith(("<", "-")) or cand.endswith((">", ".")):
                    continue
                if not PATH_TOKEN.match(cand):
                    continue
                # 形如 `R.20/R.21` 的是规则号组合，不是路径
                if all(RULE_ID_HEAD.match(seg) for seg in cand.split("/") if seg):
                    continue
                # 形如 `chNN-*.md` 是文件名通配，不是路径
                if "*" in cand:
                    continue
                checked += 1
                if any((r / cand).exists() for r in roots):
                    continue
                if kb is None:
                    # 没有知识库时，知识库内部的路径无法判定
                    kb_scoped += 1
                else:
                    missing.append(f"{rel}: {cand}")
    if missing:
        for m in sorted(set(missing)):
            fail(f"路径不存在: {m}")
    else:
        ok(f"{checked} 处路径引用全部存在")
    if kb_scoped:
        skip(f"{kb_scoped} 处路径指向知识库内部，无知识库时无法判定")


def check_rule_ids(kb) -> None:
    print("[5] 文档中引用的规则编号")
    whitelist = load_whitelist_or_fallback(kb)
    if whitelist is None:
        skip("既无知识库也无规则索引，无法校验规则编号")
        return
    total = 0
    bad = []
    targets = list(LINT_TARGETS)
    # 章节文件也进白名单校验——它们是规则号最容易写错的地方
    cdir = SKILL_DIR / "chapters"
    if cdir.is_dir():
        targets += [str(p.relative_to(SKILL_DIR)).replace("\\", "/")
                    for p in sorted(cdir.glob("ch*.md"))]
    for rel in targets:
        p = SKILL_DIR / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        errors, _ = lint_text(text, whitelist, suffix=p.suffix)
        for e in errors:
            bad.append(f"{rel}:{e['line']} {e['token']} — {e['msg']}")
        total += len(errors)
    if bad:
        for b in bad:
            fail(b)
    else:
        ok(f"全部规则编号有效（白名单 {len(whitelist)} 条）")
    print(f"        共发现 {total} 处无效编号")


def check_scripts() -> None:
    print("[6] 脚本可编译")
    # 编译产物写到临时目录，不在 skill 里留下 .pyc / __pycache__
    with tempfile.TemporaryDirectory() as tmpdir:
        for p in sorted((SKILL_DIR / "scripts").glob("*.py")) + [SKILL_DIR / "build_indexes.py"]:
            try:
                py_compile.compile(str(p), doraise=True,
                                   cfile=str(Path(tmpdir) / (p.name + ".pyc")))
                ok(f"{p.name} 语法正确")
            except py_compile.PyCompileError as exc:
                fail(f"{p.name} 语法错误: {exc}")


def check_chapters() -> None:
    """book-to-skill 形态校验：章节齐不齐、结构对不对。"""
    print("[7] 章节（book-to-skill 形态）")
    cdir = SKILL_DIR / "chapters"
    if not cdir.is_dir():
        fail("缺少 chapters/ 目录")
        return
    files = sorted(cdir.glob("ch*.md"))
    if len(files) == CHAPTER_COUNT:
        ok(f"章节数 {len(files)}")
    else:
        fail(f"章节数 {len(files)}，应为 {CHAPTER_COUNT}")

    for f in files:
        m = re.match(r"^ch(\d{2})-", f.name)
        if not m:
            fail(f"文件名不合规: {f.name}")
            continue
        text = f.read_text(encoding="utf-8")
        first = text.splitlines()[0] if text.splitlines() else ""
        if not first.startswith(f"# Chapter {int(m.group(1))}:"):
            fail(f"{f.name} 标题行异常: {first[:60]}")
        missing = [s for s in CHAPTER_REQUIRED_SECTIONS if s not in text]
        if missing:
            fail(f"{f.name} 缺小节: {', '.join(missing)}")
        if len(text) < 2500:
            fail(f"{f.name} 内容过薄（{len(text)} 字符）")
    ok(f"{len(files)} 个章节的结构已检查")


def check_skill_index() -> None:
    """SKILL.md 的章节索引必须链到真实存在的章节文件。"""
    print("[8] SKILL.md 章节索引链接")
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\((chapters/[^)]+)\)", text)
    if not links:
        fail("SKILL.md 里没有章节索引链接")
        return
    missing = [l for l in links if not (SKILL_DIR / l).is_file()]
    if missing:
        for l in missing:
            fail(f"索引指向不存在的文件: {l}")
    else:
        ok(f"{len(links)} 处章节链接全部存在")
    # 反向：每个章节文件都应该在索引里出现
    on_disk = sorted(p.name for p in (SKILL_DIR / "chapters").glob("ch*.md"))
    indexed = {l.split("/")[-1] for l in links}
    orphan = [n for n in on_disk if n not in indexed]
    if orphan:
        for n in orphan:
            fail(f"章节未进入 SKILL.md 索引: {n}")
    else:
        ok(f"磁盘上 {len(on_disk)} 个章节全部进入索引")


def check_no_bytecode() -> None:
    """skill 目录里不该有 .pyc / __pycache__——它们是构建产物，不是内容。"""
    print("[9] 无构建产物残留")
    found = [p for p in SKILL_DIR.rglob("*")
             if p.name == "__pycache__" or p.suffix == ".pyc"]
    if found:
        for p in found:
            fail(f"存在构建产物: {p.relative_to(SKILL_DIR)}")
    else:
        ok("无 .pyc / __pycache__")


def check_progressive_disclosure() -> None:
    """渐进式披露结构：L0 够瘦，四层各自有落点，且互相不重复。"""
    print("[10] 渐进式披露结构")
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    body_lines = len(text.splitlines())
    if body_lines <= L0_MAX_LINES:
        ok(f"L0（SKILL.md）{body_lines} 行 ≤ {L0_MAX_LINES}")
    else:
        fail(f"L0（SKILL.md）{body_lines} 行 > {L0_MAX_LINES}：该下沉的内容没下沉")

    # 四层各自的落点
    layers = {
        "L1 结论层": SKILL_DIR / "references" / "core-framework.md",
        "L2 专题层": SKILL_DIR / "chapters",
        "L3 原文层": SKILL_DIR / "scripts" / "kb_lookup.py",
    }
    for name, path in layers.items():
        if path.exists():
            ok(f"{name}: {path.name}")
        else:
            fail(f"{name} 落点缺失: {path.name}")

    # L0 不该再塞进整段心智模型——那属于 L1
    if "核心框架与心智模型" in text:
        fail("L0 仍含「核心框架与心智模型」整节，应下沉到 references/core-framework.md")
    else:
        ok("L0 未重复 L1 的心智模型正文")


def check_frontmatter_principles() -> None:
    """skill-forge 的 8 条书写原则里，能机器判的那几条。"""
    print("[11] frontmatter 书写原则")
    fm_mod = _import_frontmatter_validator()
    if fm_mod is None:
        skip("skill-forge 未安装，无法校验 frontmatter 原则")
        return
    try:
        fm = fm_mod.load(SKILL_DIR / "SKILL.md")
    except Exception as exc:  # noqa: BLE001
        fail(f"frontmatter 解析失败: {exc}")
        return
    warnings = fm_mod.validate_skill_frontmatter(fm, skill_dir=SKILL_DIR)
    # name 含 '+' 是已知且被用户明确接受的偏离：MiniMax Code 接受，
    # 跨宿主用 install.ps1 -SkillName <合规名> 处理。不计入失败。
    tolerable = [w for w in warnings if "kebab-case" in w]
    hard = [w for w in warnings if w not in tolerable]
    for w in tolerable:
        print(f"  WARN  {w}")
    if hard:
        for w in hard:
            fail(w)
    else:
        ok("frontmatter 符合 skill-forge 书写原则")


def _import_frontmatter_validator():
    """尽力导入 skill-forge 的 frontmatter 校验器；找不到就返回 None（降级 SKIP）。

    查找顺序：已安装的 skill-forge 包 → SKILL_FORGE_PATH 环境变量 →
    常见的同级仓库布局。都不在就降级——校验器不该成为 skill 的硬依赖。
    """
    import importlib
    import os
    try:
        return importlib.import_module("scripts._lib.frontmatter")
    except ImportError:
        pass
    candidates = []
    env = os.environ.get("SKILL_FORGE_PATH")
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve()
    candidates += [
        here.parent.parent.parent.parent / "skill-optimizer" / "skill-forge",
        here.parent.parent.parent / "skill-optimizer" / "skill-forge",
        here.parent.parent.parent.parent.parent / "skill-optimizer" / "skill-forge",
    ]
    for c in candidates:
        if (c / "scripts" / "_lib" / "frontmatter.py").is_file():
            sys.path.insert(0, str(c))
            try:
                return importlib.import_module("scripts._lib.frontmatter")
            except ImportError:
                continue
    return None


def check_route_eval() -> None:
    """章节索引路由回归：检索是否还打得准。"""
    print("[12] 章节索引路由回归")
    script = SKILL_DIR / "scripts" / "route_eval.py"
    if not script.is_file():
        skip("scripts/route_eval.py 尚未就位")
        return
    import subprocess
    r = subprocess.run([sys.executable, str(script)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    tail = (r.stdout or "").strip().splitlines()
    for line in tail[-3:]:
        if line.strip():
            print(f"        {line.strip()}")
    if r.returncode == 0:
        ok("route_eval 通过")
    else:
        fail(f"route_eval 退出码 {r.returncode}")


def inline_code_spans(line: str) -> list[str]:
    """取出行内代码片段（奇数段）。避免把两个独立代码片段之间的正文误当成一段。"""
    parts = line.split("`")
    return [p.strip() for p in parts[1::2]] if len(parts) > 1 else []


def load_whitelist_or_fallback(kb):
    """白名单优先取知识库真源；没有知识库时退回 skill 自带的规则索引。"""
    if kb is not None:
        try:
            return load_whitelist(kb)
        except FileNotFoundError:
            pass
    try:
        from rule_lint import load_whitelist_from_index
        return load_whitelist_from_index(SKILL_DIR / "references" / "rule-index.md")
    except Exception:  # noqa: BLE001
        return None


# 这些文件里的规则编号做白名单校验；rule-index.md 由生成器保证，重复校验意义不大
LINT_TARGETS = ["SKILL.md", "references/checklists.md", "references/source-map.md",
                 "references/core-framework.md", "glossary.md", "patterns.md",
                 "cheatsheet.md"]


def main() -> int:
    print(f"skill 目录: {SKILL_DIR}")
    kb = None
    try:
        kb = find_kb_root()
        print(f"知识库根目录: {kb}\n")
    except Exception:  # noqa: BLE001
        print("知识库根目录: 未找到（进入无知识库模式，仅原文检索不可用）\n")

    check_required_files()
    check_frontmatter()
    check_generated(kb)
    check_paths(kb)
    check_rule_ids(kb)
    check_scripts()
    check_chapters()
    check_skill_index()
    check_no_bytecode()
    check_progressive_disclosure()
    check_frontmatter_principles()
    check_route_eval()

    print("-" * 72)
    print(f"通过 {ok_count} 项，失败 {fail_count} 项，跳过 {skip_count} 项。")
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
