# C++ Handbook

> 给 AI 编程助手的 **C++ 知识手册**：15 章提炼 + 500 条 Core Guidelines 规则可核验 + 确定性检索路由。
> 不靠 embedding 猜，靠关键词路由命中正确的章节。

**安装名（frontmatter `name` / 仓库名）**：`cpp-handbook`

[![skill](https://img.shields.io/badge/C%2B%2B%20Handbook-2.2.0-blue)](https://github.com/kizemo/cpp-handbook)
[![tokens](https://img.shields.io/badge/load%20tier-3014%20tokens-green)](#4-它到底省了什么)
[![eval](https://img.shields.io/badge/routing%20eval-43%2F43%20pass-brightgreen)](#5-检索是可测量的)
[![license](https://img.shields.io/badge/content-CC%20BY%204.0%20%2F%20MIT-orange)](./cpp-handbook/chapters/ch14-sources.md)

### 为什么 slug 是 `cpp-handbook` 而不是 `C++-handbook`

Agent Skills 规范只允许小写字母/数字/连字符，GitHub 仓库名同样不接受 `+`
（`skill-c++` 会被 GitHub 存成 `skill-c-`）。而 **`cpp` 就是业界在"不能写 `+`"
时对 C++ 的标准 ASCII 写法**——不是我们的生造词。

本项目 20 个上游里，有 **17 个必须在仓库名里拼出 C++**，其中 **15 个用的是
`cpp` / `Cpp` / `CPP`**，只有 2 个用全拼：

| 上游 | 真实仓库名 | 拼法 |
|---|---|---|
| C++ Core Guidelines（ISO WG21 官方） | `isocpp/CppCoreGuidelines` | `Cpp` |
| C++ Best Practices | `cpp-best-practices/cppbestpractices` | `cpp` |
| Google C++ 风格指南（中文版） | `shendeguize/GoogleCppStyleGuideCN` | `Cpp` |
| Real-Time C++ | `ckormanyos/real-time-cpp` | `cpp` |
| Awesome C++ | `fffaraz/awesome-cpp` | `cpp` |
| **ISO C++ 标准草案** | `cplusplus/draft` | `cplusplus`（少数派全拼） |
| TheAlgorithms | `TheAlgorithms/C-Plus-Plus` | `C-Plus-Plus`（少数派全拼） |

反过来看，`cplusplus` 和 `cxx`（CMake 的 `CMAKE_CXX_STANDARD`、GCC 的 `-x c++` 惯例）
才是**更冷僻**的写法。完整台账见 [`knowledge-tools/sources.tsv`](./knowledge-tools/sources.tsv)，skill 内的 [`ch14-sources.md`](./cpp-handbook/chapters/ch14-sources.md)「20 个来源总览」表也逐条列出了每个上游的真实仓库名。

**面向人的界面一律写 `C++`**：本页标题、`SKILL.md` 的一级标题「C++ 编程知识手册」、
`agents/openai.yaml` 的 `display_name`。`cpp-handbook` 只是**机器读的标识符**。

---

## English summary

A **C++ knowledge skill** for AI coding agents. 15 distilled chapters from 20 authoritative
upstreams (ISO C++ WG21 Core Guidelines, Google Style, C++ Best Practices, cppreference,
learncpp, Real-Time C++), a verifiable 500-rule Core Guidelines whitelist, and a
**deterministic keyword router** that maps a user's question to exactly one chapter.

Design highlights:

- **Four-layer progressive disclosure** — index (120 tok) → hub (3 014 tok) → conclusion
  (2 494 tok, lazy) → topic chapter (lazy). You never pay for what you don't read.
- **Retrieval is a regression-tested artifact**, not a vibe: 43 routing fixtures, zero
  external dependencies, `python scripts/route_eval.py` must exit 0.
- **Works without the 1 GB knowledge base** — chapters, rule index and cheatsheets ship
  with the skill; only the deep-text lookup degrades.
- **Rule numbers are linted against a real source of truth**, not remembered.

---

## 1. 它解决什么问题

AI 写 C++ 时最常见的四种翻车：

| 症状 | 根因 | 本项目的做法 |
|---|---|---|
| 建议"用 `shared_ptr` 传参" | 记忆里没有"借用该用引用表达"这条硬约束 | 每条结论都挂 **Core Guidelines 规则号**（R.20 / F.7 / CP.8…） |
| 引用了 `Con.5`（并发的旧编号） | 规则号凭印象写，**错一位肉眼看不出来** | `rule_lint.py` 用 500 条真源白名单抓「编号不存在」和「用错章节」两类错 |
| 建议"加个 `printf` 调试" | 没有工具优先的排查顺序 | ch10 给出 编译器警告 → Sanitizer → 调试器 → 核心转储 的固定顺序 |
| 讲了一堆正确的废话 | 知识散在 20 个上游仓库里，没有消化的那层 | 15 章提炼 + 速查表 + 惯用法，**每章带代码、反模式与出处** |

> 知识库自建的第一版有 **25 处规则号错引，肉眼一条都没发现**。
> 所以「规则号必须可核对、且必须由脚本核对」是本项目的硬设计，不是锦上添花。

## 2. 价值

- **省上下文**：索引层 120 tokens、加载层 3 014 tokens（实测 tiktoken）。
  改前这一层是 4 077，常驻降 23%；具体问题只需再读 1 章。
- **省检索**：不依赖 embedding、不占共享脑锁。`kb_lookup.py` 是本地全文检索，
  即使 GBrain 脑被别的进程独占也能用。
- **省返工**：规则号、章节链接、索引新鲜度全部有可执行门禁，
  写错了当场报错而不是留给用户去发现。
- **不重复造轮子**：本 skill 是**提炼层**，不复制知识库正文。
  要条文原文回知识库，要「该怎么做」看这里——避免第二份真相源。

## 3. 快速开始

### 安装（MiniMax Code）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\cpp-handbook\install.ps1
```

脚本自动定位 skills 目录、写入 `kb_root.txt`、重写 frontmatter 里的 `name`、
并在装完后跑一次 `verify_bundle.py` 验证。装完**重开会话**即可按 `cpp-handbook` 调用。

### 安装（其它宿主）

把 `cpp-handbook/` 整个目录复制进宿主的 skills 目录即可，目录名必须与 frontmatter 的
`name` 一致：

| 宿主 | 位置 | 状态 |
|---|---|---|
| **MiniMax Code** | `~/.minimax/.minimax/skills/cpp-handbook/` | ✅ 实测可用（本仓库主力目标） |
| Claude Code | `~/.claude/skills/cpp-handbook/` | ✅ 目录式安装；`name` 需合规 |
| Codex / Cursor / OpenCode 等 | 各自主机的 skills 目录 | ✅ 目录式安装；`name` 需合规 |
| OpenAI / Codex 元数据 | — | `cpp-handbook/agents/openai.yaml` 提供 interface 描述 |

> ✅ **`name: cpp-handbook` 符合 Agent Skills 命名规范**（`^[a-z0-9][a-z0-9-]*$`，只允许小写字母/数字/连字符）。
> MiniMax Code 按 frontmatter 的 `name:` 解析，6 个跨宿主 lens
> （amp / claude / copilot / hermes / openclaw / opencode）**全部接受**，
> 不再需要 `-SkillName` 覆盖。
>
> 名字为什么是 `cpp-handbook`：① 规范；② 「C++ 手册」就是 skill 的自我定位；
> ③ 不与上游文件名撞名（Core Guidelines / C++ Best Practices / cppreference / learncpp）；
> ④ 避开旧名 `cpp-guidelines`——那会被误认成 Core Guidelines 文档本身。

### 使用

| 你说的 | 会发生什么 |
|---|---|
| "帮我 review 这段 C++ 代码" | 加载 skill → 按触发词路由到相关章 → 给出带规则号的结论 |
| "shared_ptr 循环引用怎么破" | 路由到 ch01，给出 `weak_ptr` 破环 + R.24 |
| "这段代码有没有数据竞争" | 路由到 ch05 + ch01，给出证明顺序与 TSan 验证路径 |
| "ASan 报的 heap-use-after-free 怎么查" | 路由到 ch10，给出工具排查顺序 |
| "Core Guidelines 里 R.20 说了什么" | `kb_lookup.py` 回知识库查原文（需部署知识库） |

## 4. 它到底省了什么

四层渐进式披露，**只有 L0 是常驻的**：

| 层 | 何时加载 | 内容 | 实测 token |
|---|---|---|---|
| **L0 索引** | 每个会话必付（与是否触发无关） | `name` + `description` | **120** |
| **L1 加载** | 每次触发本 skill | `SKILL.md`：路由表 + 七条铁律 + 红旗清单 | **3 014** |
| **L2 结论** | 问「整体该怎么写」 | `references/core-framework.md`（10 条心智模型详解） | 2 494（惰性） |
| **L3 专题** | 问具体问题 | `chapters/chNN-*.md` 单章 | 2 300 ~ 5 900（惰性） |
| **L4 原文** | 要条文 / API 语义 | 知识库全文检索 | 按需 |

改前 vs 改后（tiktoken 实测，脚本见 `docs/skill-forge/measure-tokens.py`）：

| | 改前 v2.0 | 改后 v2.2 | 变化 |
|---|---|---|---|
| 索引层 | 145 | **120** | -17% |
| 加载层 | 3 932 | **3 014** | -23% |
| 常驻合计 | 4 077 | **3 134** | **-23%** |
| SKILL.md 行数 | 193 | **115** | -40% |
| 心智模型正文 | 常驻 | 惰性（L2） | 按需加载 |

**一个自觉的取舍**：章节索引里的触发词表比改前多花约 60 tokens。
这是**用 token 换检索准确率**——关键词表是路由中枢，放 L0 才能保证
「一句话就能定位到一章」，不必再翻第二张索引。

## 5. 检索是可测量的

这是本项目与「随便写个 skill 目录」最大的区别：**检索有回归测试**。

```bash
python cpp-handbook/scripts/route_eval.py     # 43 条路由用例，必须全绿
```

```
通过 43 条，失败 0 条（其中歧义 0 条、缺词 0 条）
```

- `cpp-handbook/references/routing-eval.jsonl` — 43 条真实问法 → 期望章节
- `cpp-handbook/references/hero-queries.md` — 触发路由评测（正向 10 / 负向 5 / 邻接混淆 4）
- 评测脚本零外部依赖，纯 stdlib，任何机器都能跑

> 这套评测**真的抓到过东西**：首版索引表里没有「坑」「结构化绑定」「valgrind」
> 「Rule of Five」这些高频词——纯靠人工列关键词永远不会发现。
> 详见 `docs/skill-forge/audit-report.md` §5。

## 6. 可执行门禁（不要靠自觉）

```bash
python cpp-handbook/scripts/verify_bundle.py   # 41 项：索引陈旧 / 指针失效 / 渐进式披露结构
python cpp-handbook/scripts/selftest.py        # 25 项：脚本行为 + 无知识库降级
python cpp-handbook/scripts/rule_lint.py .     # 规则号 lint（500 条真源白名单）
python cpp-handbook/scripts/kb_lookup.py "ownership shared_ptr cycle" --top 6
```

`verify_bundle.py` 覆盖 12 组检查，其中第 10 组专查**渐进式披露结构**
（L0 是否超过 150 行、L1/L2/L3 是否各有落点、L0 是否又抄了一遍 L1 的正文）。

## 7. 目录结构

```
cpp-handbook/
├── README.md                  ← 你正在读的这份
├── cpp-handbook/                 ← skill 本体（复制这个目录去安装）
│   ├── SKILL.md               ← L0 常驻层：路由表 + 铁律 + 红旗
│   ├── chapters/              ← L3 专题层：ch01–ch15
│   ├── references/
│   │   ├── core-framework.md  ← L2 结论层：10 条心智模型
│   │   ├── rule-index.md      ← 500 条规则号索引（生成物）
│   │   ├── source-map.md      ← 问题类型 → 知识库位置（生成物）
│   │   ├── checklists.md      ← 分环节自检清单
│   │   ├── hero-queries.md    ← 触发路由评测集
│   │   └── routing-eval.jsonl ← 章节路由评测集
│   ├── glossary.md            ← 术语表
│   ├── patterns.md            ← 手法与惯用法
│   ├── cheatsheet.md          ← 决策表与速查
│   ├── scripts/               ← 可执行校验层（纯 stdlib + Python 3.9+）
│   ├── build_indexes.py       ← 索引层生成器
│   ├── install.ps1            ← 一键安装（ASCII-only，PS 5.1 安全）
│   ├── agents/openai.yaml
│   └── skillopt-benchmark.jsonl
├── knowledge-tools/           ← 知识库的可复现工具（本体 1GB，不进仓库）
├── docs/
│   ├── skill-forge/           ← 本轮优化的完整审计报告与 token 实测
│   └── book-to-skill/         ← 知识库 → skill 的转换记录
└── .gitignore
```

## 8. 可选：知识库

本 skill **不需要**知识库就能工作（章节、规则索引、速查表都在 skill 里）。
知识库是可选增强——约 1GB 的 20 个上游仓库原文快照，用于查**条文原文**。

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

## 9. 适配的 AI agents 架构

本项目不是"给某个 agent 写的一份提示词"，而是按 **Agent Skills 规范**
（`SKILL.md` + frontmatter + 可选的 `scripts/` `references/` `assets/`）构建的
**上下文预编译产物**。它对 agent 的价值在于把三件事前置：

1. **路由前置**：把「该读哪一段」从模型的模糊联想，变成一张关键词 → 章节的确定性映射。
   省掉的不只是 token，还有**读错章的概率**。
2. **检索前置**：把 RAG 的"向量召回 + 重排 + 脑锁依赖"换成
   **本地全文检索 + 真源白名单**。本地、可离线、无外部依赖、可回归测试。
3. **质量前置**：规则号、链接、索引新鲜度都在**提交前**由脚本判定，
   而不是让用户在 review 时才发现引用错了编号。

三层宿主接口约定：

| 接口层 | 文件 | 何时被读取 |
|---|---|---|
| **索引层** | `SKILL.md` 的 frontmatter（`name` / `description` / `triggers`） | 每个会话，宿主扫描 skills 目录时 |
| **加载层** | `SKILL.md` 正文 | skill 被触发时 |
| **运行层** | `chapters/` `references/` `scripts/` | agent 自己决定何时读 |

> **渐进式披露不是口号，是可校验的**：`verify_bundle.py` 第 10 组会检查
> L0 是否超 150 行、四层是否各有落点、L0 是否重复了 L1 的正文。
> 违反就红。

## 10. 开发

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

工作流用的两个外部工具链：

- **[book-to-skill](https://github.com/kizemo/book-to-skill)** — 把文档/知识库转成章节式 skill
  （抽取 → 结构分析 → 生成 → 校验 → 清理），转换记录在 `docs/book-to-skill/`。
- **[skill-forge](https://github.com/kizemo/skill-forge)** — 六相优化管道
  （审计 → 定范围 → 基准 → forward → 三判官 → 物化），
  本轮优化报告在 `docs/skill-forge/audit-report.md`。

## 11. 来源与许可

内容来自 20 个公开上游（完整台账见 `cpp-handbook/chapters/ch14-sources.md` 与
`knowledge-tools/sources.tsv`），其中包括 ISO C++ WG21 **Core Guidelines**、
**Google C++ Style Guide**、**C++ Best Practices**、**cppreference**、
**learncpp.com**、**Real-Time C++** 等。

各上游的原始许可随其内容保留；本仓库的 skill 正文为**提炼与再组织**，
发布前请核对 `ch14-sources.md` 中的逐项许可条款。

> 引用 Core Guidelines 规则时请注明出处：
> [CppCoreGuidelines](https://github.com/isocpp/CppCoreGuidelines)
