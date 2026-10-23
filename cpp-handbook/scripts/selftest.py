#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill 自检：用合成样例验证三个脚本的行为。

这不是形式主义的单元测试——每个断言都对应一个**实测踩过的坑**：
- 规则号写错必须报错（知识库首稿有 25 处错引，没有任何工具报出来）
- 编号存在但用错章节必须给提示（并发规则写成 Con.* 而非 CP.*）
- 检索不得把「部分命中」整池丢弃（英文词命中不了中文正文）

用法：
    python selftest.py
退出码 0 = 全通过，1 = 有失败。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_DIR / "scripts"

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}" + (f"  —— {detail}" if detail else ""))


def run(script: str, *args: str) -> tuple[int, str]:
    return run_in(SKILL_DIR, script, *args)


def run_in(base: Path, script: str, *args: str) -> tuple[int, str]:
    """在指定 skill 根目录下跑一个脚本（用于无知识库降级测试）。"""
    proc = subprocess.run(
        [sys.executable, str(base / "scripts" / script), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
        cwd=str(base))
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="cpp-skill-selftest-"))
    print(f"临时目录: {tmp}\n")

    print("[1] rule_lint：无效规则号必须报错（文档在讨论 Core Guidelines 时）")
    bad = tmp / "bad-rules.md"
    bad.write_text(
        "# 测试\n\n"
        "本文档依据 Core Guidelines 整理规则引用。\n\n"
        "- 并发规则见 CP.2（避免数据竞争）\n"
        "- 这条编号不存在：CP.999\n"
        "- 前缀根本不存在：M.5\n"
        "- 这条存在：R.11\n",
        encoding="utf-8")
    code, out = run("rule_lint.py", str(bad))
    check("退出码为 1", code == 1, f"实际 {code}")
    check("报出 CP.999", "CP.999" in out)
    check("报出 M.5", "M.5" in out)
    check("R.11 未出现在 ERROR 行",
          not any("R.11" in l and l.startswith("ERROR") for l in out.splitlines()))

    print("\n[1b] rule_lint：非 Core Guidelines 文档只提示不报错")
    other = tmp / "other-numbering.md"
    other.write_text(
        "# 测试\n\n"
        "- 见 A.3 附录\n"
        "- 见 M.5 课时\n",
        encoding="utf-8")
    code, out = run("rule_lint.py", str(other))
    check("退出码为 0", code == 0, f"实际 {code}")
    check("仍给出提示", "A.3" in out or "M.5" in out)

    print("\n[2] rule_lint：编号存在但章节用错必须提示")
    wrong = tmp / "wrong-chapter.md"
    wrong.write_text(
        "# 测试\n\n"
        "- 并发数据竞争要避免，见 Con.2\n"
        "- 所有权用智能指针表达，见 R.20\n",
        encoding="utf-8")
    code, out = run("rule_lint.py", str(wrong))
    check("Con.2 给出语义提示", "Con.2" in out and "CP." in out)
    check("R.20 不被误报",
          not any("R.20" in l and ("WARN" in l or "ERROR" in l)
                  for l in out.splitlines()))

    print("\n[3] kb_lookup：部分命中不得被整池丢弃")
    code, out = run("kb_lookup.py", "ownership", "--top", "20")
    check("退出码为 0", code == 0, f"实际 {code}")
    check("命中了中文主题页 ownership-and-lifetime",
          "ownership-and-lifetime" in out, out[:400])

    print("\n[4] verify_bundle：skill 自身一致性")
    code, out = run("verify_bundle.py")
    check("退出码为 0", code == 0, out[-800:])
    check("失败 0 项", "失败 0 项" in out, out[-300:])

    print("\n[5] build_indexes --check：索引层不得陈旧")
    proc = subprocess.run(
        [sys.executable, str(SKILL_DIR / "build_indexes.py"), "--check"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    check("退出码为 0", proc.returncode == 0, proc.stdout[-400:])

    print("\n[6] route_eval：章节索引路由回归必须全过")
    code, out = run("route_eval.py")
    check("退出码为 0", code == 0, out[-400:])
    check("失败 0 条", "失败 0 条" in out, out[-300:])

    print("\n[7] 渐进式披露：L0 够瘦，L1/L2/L3 都有落点")
    skill_md = SKILL_DIR / "SKILL.md"
    body_lines = len(skill_md.read_text(encoding="utf-8").splitlines())
    check(f"SKILL.md {body_lines} 行 ≤ 150", body_lines <= 150, f"实际 {body_lines}")
    check("L1 结论层存在", (SKILL_DIR / "references" / "core-framework.md").is_file())
    check("L2 专题层存在", (SKILL_DIR / "chapters").is_dir())
    check("L3 原文层入口存在", (SKILL_DIR / "scripts" / "kb_lookup.py").is_file())

    print("\n[8] 无知识库时 skill 必须仍能工作（降级为 SKIP 而不是 FAIL）")
    nokb = tmp / "nokb" / "a" / "cpp-handbook"
    nokb.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL_DIR, nokb, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    code, out = run_in(nokb, "verify_bundle.py")
    check("verify_bundle 退出码为 0", code == 0, out[-600:])
    check("出现 SKIP（真源比对降级）", "SKIP" in out, out[-400:])
    check("没有 FAIL", "FAIL" not in out, out[-600:])

    print("\n[9] 无知识库时 rule_lint 仍能报出无效规则号（白名单回退到自带索引）")
    code, out = run_in(nokb, "rule_lint.py", str(bad))
    check("退出码为 1", code == 1, f"实际 {code}")
    check("仍报出 CP.999", "CP.999" in out, out[-300:])
    check("白名单来自 skill 自带索引", "无知识库" in out, out[-300:])

    print("-" * 72)
    print(f"通过 {passed} 项，失败 {failed} 项。")
    print(f"（临时文件留在 {tmp}，可自行删除）")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
