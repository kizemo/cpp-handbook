#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库根目录解析（skill 内部共享模块）。

skill 被部署到 ~/.minimax/.minimax/skills/ 后，与 knowlege/ 不在同一棵目录树下，
因此不能靠相对路径猜。这里按优先级依次尝试：

1. 环境变量 ``CPP_KB_ROOT``
2. skill 目录下的标记文件 ``kb_root.txt``（安装脚本写入绝对路径）
3. skill 目录的同级/子级 ``knowlege``（仓库内直接使用时的布局）

任何候选必须同时含有 ``index/knowledge-map.md`` 与 ``topics/`` 才算有效。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# 不在 skill 目录里留下 __pycache__
sys.dont_write_bytecode = True

SKILL_DIR = Path(__file__).resolve().parent.parent


class KbNotFound(RuntimeError):
    """找不到知识库根目录。"""


def _looks_like_kb(p: Path) -> bool:
    try:
        return (p / "index" / "knowledge-map.md").is_file() and (p / "topics").is_dir()
    except OSError:
        return False


def candidates() -> list[Path]:
    out: list[Path] = []
    env = os.environ.get("CPP_KB_ROOT")
    if env:
        out.append(Path(env))
    marker = SKILL_DIR / "kb_root.txt"
    if marker.is_file():
        try:
            out.append(Path(marker.read_text(encoding="utf-8").strip()))
        except OSError:
            pass
    out.append(SKILL_DIR.parent / "knowlege")
    out.append(SKILL_DIR / "knowlege")
    out.append(SKILL_DIR.parent.parent / "knowlege")
    return out


def find_kb_root() -> Path:
    tried = []
    for c in candidates():
        tried.append(str(c))
        if c and _looks_like_kb(c):
            return c.resolve()
    raise KbNotFound(
        "找不到知识库根目录。已尝试：\n  " + "\n  ".join(tried) +
        "\n解决办法：设置环境变量 CPP_KB_ROOT 指向 knowlege 目录，"
        "或在 skill 目录下写一个 kb_root.txt（内容为该目录的绝对路径）。"
    )


def kb_root_or_none() -> Path | None:
    try:
        return find_kb_root()
    except KbNotFound:
        return None


def relative_to_kb(p: Path, kb: Path) -> str:
    try:
        return str(p.relative_to(kb)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")
