# book-to-skill 转换记录

> 2026-10-22 · 把 `knowlege/` 知识库的**消化层**转成章节式 skill。

## 跑了什么

```bash
BOOK_SKILL_WORKDIR=C:/Users/Duanyi/AppData/Local/Temp/b2s-cpp-work \
  python C:/Users/Duanyi/.claude/skills/book-to-skill/scripts/extract.py
```

| 阶段 | 结果 |
|---|---|
| 环境预检 | 通过 |
| 抽取 | 16 源 / 129 KB / 11 153 词 / ≈25K tokens |
| 结构分析 | 11 篇主题页 + 4 篇索引页 → 15 章 |
| 生成 | ch01–ch11 并行 worker，ch12–ch15 自写 |
| 校验 | 官方 `scan_generated_skill.py` 通过，无注入/越权 |
| 清理 | 临时工作目录已删除 |

## 输入范围判断

只纳入**消化层**（`topics/` 11 篇 + `index/` 4 篇 + `README.md`）。
上游 1 056 篇 / 19.3 MB **未纳入**——500 条规则会让章节检测爆到 500 章。
上游原文由 `scripts/kb_lookup.py` 覆盖，是**运行时检索层**，不是生成输入。

## 本目录的文件

| 文件 | 作用 |
|---|---|
| `chapter-template.md` | 章节模板（7 个必备小节 + 抽取卡） |
| `chapters-plan.md` | 15 章的分工计划（给并行 worker 的共同契约） |
| `check_chapters.py` | 章节结构检查 |
| `count_tokens.py` | tiktoken 精确计量（SKILL.md 硬约束 < 4000） |

## 校验结果（转换完成时）

- SKILL.md：3932 cl100k / 3322 o200k（硬约束 < 4000，达标）
- 章节：1868–5162 o200k / 章（密度优先于长度）
- 核心层合计：58 293 o200k
- `rule_lint.py`：19 个文件 **0 错误 0 提示**
- `verify_bundle.py`：32/32 通过（v2.1 时扩到 41 项）
- `selftest.py`：13/13 通过（v2.1 时扩到 25 项）

> 本轮 skill-forge 优化把 SKILL.md 压到 3 014 cl100k / 115 行，
> 详见 [`../skill-forge/audit-report.md`](../skill-forge/audit-report.md)。
