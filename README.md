# C++ Handbook

> 给 AI 编程助手的 **C++ 知识手册**：15 章提炼 + 500 条 Core Guidelines 规则可核验 + 确定性检索路由。
> 不靠 embedding 猜，靠关键词路由命中正确的章节。

[![skill](https://img.shields.io/badge/Agent%20Skill-cpp--handbook-2.2.0-blue)](./cpp-handbook/SKILL.md)
[![tokens](https://img.shields.io/badge/resident%20context-3%20135%20tokens-green)](#它到底占多少上下文)
[![eval](https://img.shields.io/badge/routing%20eval-43%2F43%20pass-brightgreen)](#质量是测出来的)
[![gates](https://img.shields.io/badge/self-checks-41%20%2B%2025%20pass-blue)](#质量是测出来的)
[![license](https://img.shields.io/badge/content-CC%20BY%204.0%20%2F%20MIT-orange)](./cpp-handbook/chapters/ch14-sources.md)

**安装名**：`cpp-handbook`（符合 Agent Skills 规范 `^[a-z0-9][a-z0-9-]*$`；目录名须与之一致）

<details>
<summary><b>English</b></summary>

A **C++ knowledge skill** for AI coding agents: 15 distilled chapters built from 20 authoritative
upstreams (ISO C++ WG21 Core Guidelines, Google Style, C++ Best Practices, cppreference,
learncpp, Real-Time C++), a **verifiable 500-rule** Core Guidelines whitelist, and a
**deterministic keyword router** that maps a question to exactly one chapter.

- **Four-layer progressive disclosure** — index (120 tok) → hub (3 014 tok) → conclusion
  (2 494 tok, lazy) → topic chapter (lazy). You never pay for what you don't read.
- **Retrieval is regression-tested**, not a vibe: 43 routing fixtures, zero external
  dependencies, `python scripts/route_eval.py` must exit 0.
- **Works without the 1 GB knowledge base** — chapters, rule index and cheatsheets ship
  with the skill; only the deep-text lookup degrades.
- **Rule numbers are linted against a real source of truth**, not remembered.

</details>

---

## 30 秒上手

```bash
git clone https://github.com/kizemo/cpp-handbook.git
cp -r cpp-handbook/cpp-handbook ~/.claude/skills/     # 或你的宿主目录
```

装完重开一个会话，直接用自然语言提 C++ 问题即可——宿主会按 frontmatter 的
`name: cpp-handbook` 匹配到本 skill。Windows / MiniMax Code 有现成脚本：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\cpp-handbook\install.ps1
```

脚本会定位 skills 目录、写入知识库指针、重写 frontmatter 的 `name`，
并在装完后跑一次 `verify_bundle.py` 验证。

## 为什么不是直接问 LLM

AI 写 C++ 时最常见的四种翻车——这个 skill 就是为修这四件事做的：

| 症状 | 根因 | 本项目的做法 |
|---|---|---|
| 建议"用 `shared_ptr` 传参" | 记忆里没有"借用该用引用表达"这条硬约束 | 每条结论都挂 **Core Guidelines 规则号**（R.20 / F.7 / CP.8…） |
| 引用了 `Con.5`（并发的旧编号） | 规则号凭印象写，**错一位肉眼看不出来** | `rule_lint.py` 用 500 条真源白名单抓「编号不存在」和「用错章节」两类错 |
| 建议"加个 `printf` 调试" | 没有工具优先的排查顺序 | ch10 给出 编译器警告 → Sanitizer → 调试器 → 核心转储 的固定顺序 |
| 讲了一堆正确的废话 | 知识散在 20 个上游仓库里，没有消化的那层 | 15 章提炼 + 速查表 + 惯用法，**每章带代码、反模式与出处** |

> 我们自己建知识库的第一版有 **25 处规则号错引，肉眼一条都没发现**。
> 所以「规则号必须可核对、且必须由脚本核对」是这个 skill 的硬设计，不是锦上添花。

差别不在"内容更多"，而在三件前置的事：

1. **路由前置**——把"该读哪一段"从模型的模糊联想，变成一张关键词 → 章节的确定性映射。省掉的不只是 token，还有**读错章的概率**。
2. **检索前置**——把 RAG 的"向量召回 + 重排 + 脑锁依赖"换成**本地全文检索 + 真源白名单**：本地、可离线、无外部依赖、可回归测试。
3. **质量前置**——规则号、链接、索引新鲜度都在**提交前**由脚本判定，而不是让用户在 review 时才发现引用错了编号。

## 装到你的 agent 里

按 [Agent Skills 规范](https://agentskills.io) 组织：`SKILL.md` + frontmatter + 可选的
`scripts/` `references/`。把 `cpp-handbook/` 整个目录复制进宿主的 skills 目录即可。

| 宿主 | 位置 | 状态 |
|---|---|---|
| **MiniMax Code** | `~/.minimax/.minimax/skills/cpp-handbook/` | ✅ 实测可用（`install.ps1` 一键装） |
| Claude Code | `~/.claude/skills/cpp-handbook/` | ✅ 目录式安装 |
| Codex / Cursor / OpenCode 等 | 各自主机的 skills 目录 | ✅ 目录式安装 |
| OpenAI / Codex 元数据 | — | `cpp-handbook/agents/openai.yaml` 提供 interface 描述 |

宿主按 frontmatter 的 `name:` 解析 skill，**不看目录名**——所以目录名必须与
`name: cpp-handbook` 一致。想装成别的名字，用 `install.ps1 -SkillName <名字>`
（会同步重写 frontmatter）。

### 装好之后会怎样

| 你说的 | 会发生什么 |
|---|---|
| "帮我 review 这段 C++ 代码" | 加载 skill → 按触发词路由到相关章 → 给出带规则号的结论 |
| "shared_ptr 循环引用怎么破" | 路由到 ch01，给出 `weak_ptr` 破环 + R.24 |
| "这段代码有没有数据竞争" | 路由到 ch05 + ch01，给出证明顺序与 TSan 验证路径 |
| "ASan 报的 heap-use-after-free 怎么查" | 路由到 ch10，给出工具排查顺序 |
| "Core Guidelines 里 R.20 说了什么" | `kb_lookup.py` 回知识库查原文（需部署知识库） |

## 里面有什么

**15 章**（`cpp-handbook/chapters/`），每章结构一致：核心思想 → 框架 → 概念 →
心智模型 → 反模式 → 代码 → 参考表 → 实例 → 要点 → 关联章节。

| 章 | 主题 | 章 | 主题 |
|---|---|---|---|
| ch01 | 所有权与生命周期 | ch09 | 工程实践（CMake / 测试 / CI） |
| ch02 | 移动语义与完美转发 | ch10 | 工具链与调试（Sanitizer / 转储） |
| ch03 | 模板与 Concepts | ch11 | 陷阱与反模式 |
| ch04 | STL 容器与算法 | ch12 | 案例索引（算法题解） |
| ch05 | 并发编程 | ch13 | 学习路线 |
| ch06 | 错误处理 | ch14 | 来源台账 |
| ch07 | 性能优化 | ch15 | 知识地图与库结构 |
| ch08 | 现代 C++ 特性全景 | | |

配套速查：`cheatsheet.md`（9 张决策表）· `patterns.md`（19 个惯用法）·
`glossary.md`（术语）· `references/checklists.md`（分环节自检清单）·
`references/rule-index.md`（500 条规则号索引）· `references/source-map.md`（问题类型 → 知识库位置）。

## 它到底占多少上下文

四层渐进式披露，**只有 L0 是常驻的**：

| 层 | 何时加载 | 内容 | 实测 token |
|---|---|---|---|
| **L0 索引** | 每个会话必付（与是否触发无关） | `name` + `description` | **120** |
| **L1 加载** | 每次触发本 skill | `SKILL.md`：路由表 + 七条铁律 + 红旗清单 | **3 014** |
| **L2 结论** | 问「整体该怎么写」 | `references/core-framework.md`（10 条心智模型详解） | 2 494（惰性） |
| **L3 专题** | 问具体问题 | `chapters/chNN-*.md` 单章 | 2 300 ~ 5 900（惰性） |
| **L4 原文** | 要条文 / API 语义 | 知识库全文检索 | 按需 |

**常驻合计 3 135 tokens**（实测 tiktoken）；具体问题只需再读 1 章。
数值可用 `python docs/skill-forge/measure-tokens.py` 复算。

一个自觉的取舍：章节索引里的触发词表比"只有标题"多花约 60 tokens。
这是**用 token 换检索准确率**——关键词表是路由中枢，放 L0 才能保证
"一句话就能定位到一章"，不必再翻第二张索引。

## 质量是测出来的

这是本项目与"随便写个 skill 目录"最大的区别：**检索有回归测试，写错了会红**。

```bash
python cpp-handbook/scripts/verify_bundle.py   # 41 项：索引陈旧 / 指针失效 / 渐进式披露结构
python cpp-handbook/scripts/selftest.py        # 25 项：脚本行为 + 无知识库降级
python cpp-handbook/scripts/route_eval.py      # 43 条路由用例，必须全绿
python cpp-handbook/scripts/rule_lint.py .     # 规则号 lint（500 条真源白名单）
python cpp-handbook/scripts/kb_lookup.py "ownership shared_ptr cycle" --top 6
```

- `verify_bundle.py` 覆盖 12 组检查，其中第 10 组专查**渐进式披露结构**
  （L0 是否超 150 行、四层是否各有落点、L0 是否又抄了一遍 L1 的正文）。
- `route_eval.py` 跑 `references/routing-eval.jsonl` 的 **43 条真实问法**，
  校验"这句话该落到哪一章"。零外部依赖，纯 stdlib，任何机器都能跑。
- `references/hero-queries.md` 是另一层评测：判断"这个提问**该不该**触发本 skill"
  （正向 10 / 负向 5 / 邻接混淆 4）。

> 这套评测**真的抓到过东西**：首版索引表里没有「坑」「结构化绑定」「valgrind」
> 「Rule of Five」这些高频词——纯靠人工列关键词永远不会发现。
> 详见 [`docs/skill-forge/audit-report.md`](./docs/skill-forge/audit-report.md) §5。

## 可选：1 GB 知识库

本 skill **不需要**知识库就能工作（章节、规则索引、速查表都随 skill 分发）。
知识库是可选增强——20 个上游仓库的原文快照，用于查**条文原文**。

| | 有知识库 | 无知识库 |
|---|---|---|
| 章节 / 速查 / 规则索引 | ✅ | ✅ |
| `rule_lint.py` 规则号校验 | ✅ 用真源 | ✅ 回退到自带索引副本 |
| `kb_lookup.py` 原文检索 | ✅ | ⚠️ 明确报错（exit 2），不崩 |
| `verify_bundle.py` | ✅ 41 项 | ✅ 39 项 + 2 项 SKIP（真源比对降级） |

启用方式（二选一）：

```bash
export CPP_KB_ROOT=/path/to/knowlege      # 环境变量
# 或在 skill 目录写 kb_root.txt，内容为 knowlege 的绝对路径
```

## 扩展与开发

```bash
# 改了 SKILL.md / 章节后，跑全套门禁
python cpp-handbook/scripts/verify_bundle.py
python cpp-handbook/scripts/selftest.py
python cpp-handbook/scripts/route_eval.py

# 改了知识库后，重建索引层（生成物禁止手改）
python cpp-handbook/build_indexes.py            # 重建
python cpp-handbook/build_indexes.py --check    # 只比对

# token 计量
python docs/skill-forge/measure-tokens.py
```

`knowledge-tools/` 收录了知识库的**可复现工具**（规则清单重建、检索评测、双链检查、
来源台账）——想建自己同规格知识库的话，从这里开始。

工作流用的两个外部工具链：

- **[book-to-skill](https://github.com/virgiliojr94/book-to-skill)** — 把文档/知识库转成章节式 skill
  （抽取 → 结构分析 → 生成 → 校验 → 清理），转换记录在 [`docs/book-to-skill/`](./docs/book-to-skill/)。
- **[skill-forge](https://github.com/kizemo/skill-forge)** — 六相优化管道
  （审计 → 定范围 → 基准 → forward → 三判官 → 物化），
  本项目 v2.2 的完整优化报告在 [`docs/skill-forge/audit-report.md`](./docs/skill-forge/audit-report.md)。

### 目录结构

```
cpp-handbook/
├── README.md                  ← 你正在读的这份
├── cpp-handbook/              ← skill 本体（复制这个目录去安装）
│   ├── SKILL.md               ← L0 常驻层：路由表 + 铁律 + 红旗
│   ├── chapters/              ← 15 章
│   ├── references/            ← 心智模型 / 规则索引 / 来源路由 / 评测集
│   ├── glossary.md  patterns.md  cheatsheet.md
│   ├── scripts/               ← 可执行校验层（纯 stdlib + Python 3.9+）
│   ├── build_indexes.py       ← 索引层生成器
│   ├── install.ps1            ← 一键安装（ASCII-only，PS 5.1 安全）
│   ├── agents/openai.yaml
│   └── skillopt-benchmark.jsonl
├── knowledge-tools/           ← 知识库的可复现工具（本体 1GB，不进仓库）
└── docs/
    ├── skill-forge/           ← 优化审计报告与 token 实测
    └── book-to-skill/         ← 知识库 → skill 的转换记录
```

## 来源与许可

内容来自 20 个公开上游（逐项台账见
[`cpp-handbook/chapters/ch14-sources.md`](./cpp-handbook/chapters/ch14-sources.md) 与
[`knowledge-tools/sources.tsv`](./knowledge-tools/sources.tsv)），其中包括 ISO C++ WG21
**Core Guidelines**、**Google C++ Style Guide**、**C++ Best Practices**、**cppreference**、
**learncpp.com**、**Real-Time C++** 等。

各上游的原始许可随其内容保留；本仓库的 skill 正文为**提炼与再组织**，
使用前请核对 `ch14-sources.md` 中的逐项许可条款。

> 引用 Core Guidelines 规则时请注明出处：
> [CppCoreGuidelines](https://github.com/isocpp/CppCoreGuidelines)
