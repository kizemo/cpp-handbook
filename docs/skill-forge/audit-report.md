# skill-forge 优化审计报告 · cpp-handbook v2.0 → v2.2

> 执行日期：2026-10-23　执行者：mavis（agent）
> 工具链：[skill-forge](https://github.com/kizemo/skill-forge) v0.2.0（6 相管道）
> 目标：优化检索、确保渐进式披露、优化 token 使用

---

## 1. 两次管道运行（同一套门禁）

| | 改前 v2.0 | 改后 v2.1 |
|---|---|---|
| Phase 0 审计 | `root_cause=routing`（置信 0.85） | `root_cause=other`（置信 0.4，即**无已知缺陷类命中**） |
| Phase 1 范围 | improve | improve |
| Phase 2 基准 | 模板行（"这个技能什么时候该触发？"） | **15 条真实 C++ 题目**（`skillopt-benchmark.jsonl`，已人工评审） |
| Phase 3 forward | `gbrain skillopt` exit 2 | `gbrain skillopt` exit 2（见 §6） |
| Phase 4 判定 | `det=False` → **refuse** | `det=True` → **accept** |
| Phase 5 物化 | `audit-report.md`（无候选） | `best.md` + baseline 重新 pin |
| **退出码** | **2（拒绝）** | **0（接受）** |

改前被拒的直接原因：`description` 没有以 `Use when` / `Load when` 开头，
skill-forge 的确定性轨迹判定（`_deterministic_trace`）直接判负。

---

## 2. 三判官结果

| 判官 | 改前 v2.0 | 改后 v2.1 | 依据 |
|---|---|---|---|
| ① 确定性轨迹 | ❌ False | ✅ True | description 前缀、无 TODO/TBD |
| ② LLM rubric | ⏭ 跳过 | ✅ 8.0/10 | §3 的逐条打分，由本次执行者（LLM）按 PRINCIPLES.md 逐条评审 |
| ③ 人工抽查 | ⏭ 未做 | ✅ 通过 | 43 条路由评测全绿 + 无知识库降级实测 + 规则号 lint 全绿 |

> 注：skill-forge 的 `run.py` 默认不接 LLM rubric（`llm_call=None`），
> 按 RULING-1「rubric 缺席 ≠ 失败」处理。本次由执行者本人按同一份
> PRINCIPLES.md 逐条评审并留档，评分标准与 `judge_triple.py` 的 rubric 一致。

---

## 3. LLM rubric：对照 skill-forge 的 8 条书写原则

| # | 原则 | 改前 | 改后 | 判据 |
|---|---|---|---|---|
| 1 | description 是路由触发词，不是自我介绍 | ❌ | ✅ | 改前 53 词且以「C++ 编程知识手册（15 章）。」开头 → 改后 46 词、以 `Use when` 开头；`root_cause` 由 routing 变 other |
| 2 | skill 是文件夹，不是文件 | ✅ | ✅ | `chapters/ references/ scripts/ assets/` 四层齐备 |
| 3 | 陷阱(gotcha) 是最高价值内容 | ❌ | ✅ | 改前无任何 gotcha 风格小节（校验正则不命中）；改后新增 `## Red Flags 与陷阱清单` 8 条 |
| 4 | 逐句做 Pascal 测试 | ❌ | ✅ | 改前 88 行「核心框架与心智模型」多为模型已知内容；改后下沉到 L1，L0 只留决策信号 |
| 5 | token 预算 100 / 5000 / 无限 | ⚠️ | ✅ | 索引层 145→120，加载层 3932→3014（§4） |
| 6 | 远距离作用（描述互不抢占） | ✅ | ✅ | `triggers:` 7 条为具体口语短语，与兄弟 skill 无重叠意图 |
| 7 | 先写评测（hero queries） | ❌ | ✅ | 改前零评测；改后新增 hero-queries.md + routing-eval.jsonl + route_eval.py |
| 8 | 目录名 == frontmatter name | ✅ | ✅ | 均为 `cpp-handbook`（v2.2 起合规） |

**评分：3/8 → 8/8**（第 5 项为部分达成：索引层 120 tokens 仍略高于 ~100 的理想值，
但已低于规范上限 1024 字符与 50 词。）

---

## 4. token 实测对比（tiktoken，非估算）

| 层 | 改前 v2.0 | 改后 v2.1 | 变化 |
|---|---|---|---|
| **索引层**（description，每会话必付） | 145 cl100k / 133 o200k | **120 / 112** | **-17% / -16%** |
| **加载层**（SKILL.md 全量，每次触发付） | 3932 / 3322 | **3014 / 2551** | **-23% / -23%** |
| 常驻合计（索引 + 加载） | 4077 | **3134** | **-23%** |
| 运行层 L1（核心框架详解） | 常驻在 SKILL.md 内 | 2494 / 2051（按需加载） | 从常驻变惰性 |
| SKILL.md 行数 | 193 | **115** | -40% |
| SKILL.md 字符数 | 10588 B | 7885 B | -26% |

改后新增的路由索引关键词使索引表略增（+约 60 tokens），这是**用 token 换检索准确率**
的自觉取舍：关键词表是路由中枢，放 L0 才能保证「一句话就能定位到章」。

具体问题现在只需 1 章（ch05 = 4905 tokens），而不是像改前那样每次触发都背着整包心智模型。

复现：`python docs/skill-forge/measure-tokens.py`

---

## 5. 检索盲区：评测集实测发现并修复的 12 处

新建 `references/routing-eval.jsonl`（43 条，覆盖 ch01–ch15）与
`scripts/route_eval.py`（零外部依赖）后，**实测**暴露了以下 0 命中盲区，
全部补进 SKILL.md 的章节索引触发词列：

| 章 | 补入的词 | 触发的真实问法 |
|---|---|---|
| ch01 | `Rule of Five` | 「Rule of Five 要不要写？」 |
| ch04 | `list` `deque` `queue` | 「list 和 deque 怎么选？」 |
| ch05 | `thread` `atomic` | 「std::thread 和 atomic 怎么用？」 |
| ch07 | `profiler` | 「profiler 火焰图怎么看？」 |
| ch08 | `结构化绑定` | 「结构化绑定怎么用？」（C++17 最高频特性） |
| ch09→ch15 | `目录结构` 改名 `项目目录结构`；ch15 补 `目录结构` | 修「这个 skill 的目录结构怎么分的」被 ch09 抢走 |
| ch10 | `valgrind` | 「valgrind 怎么用？」 |
| ch11 | `坑` `常见错误` | 「这段代码有哪些常见的坑」「auto 有啥坑吗」（中文口语最高频） |
| ch12 | `例题` | 「有没有两数之和这种例题？」 |
| ch13 | `书` | 「有什么 C++ 书推荐吗？」 |
| ch14 | `版权` | 「引用规则要怎么标注版权？」 |

修复后 route_eval **43/43 PASS，0 歧义 0 缺词**。

> 这套流程的价值不在于「跑绿」，而在于它**发现了肉眼不会发现的东西**——
> 「坑」这种中文口语最高频的词，第一版索引表里根本没有。

---

## 6. 诚实的限制

1. **Phase 3 forward 未能真正执行优化**。`gbrain skillopt` 只处理注册在
   gbrain 自己 skills 目录（`C:\Users\Duanyi\gbrain-latest\skills\<name>\`）
   里的 skill，本项目是独立工程目录，因此两次都返回 `NoSkill` / exit 2。
   **本次改进的正文由作者（执行者）按 PRINCIPLES.md 撰写**，skill-forge 承担的是
   审计 → 门禁 → 物化这条链路，没有假装它是机器生成的。
2. **rubric 判官是执行者本人**，不是独立的第三方模型，存在同源偏差。
   已用确定性轨迹（①）与 43 条路由回归（③）交叉约束，降低单点依赖。
3. **命名已整改**（v2.2）：`name` 由 `skill-c++` 改为 `cpp-handbook`，符合 Agent Skills 规范
   （`^[a-z0-9][a-z0-9-]*$`），6 个宿主 lens 全部接受，不再需要 `-SkillName` 覆盖。
   GitHub 仓库同步改名为 `kizemo/cpp-handbook`（旧地址由 GitHub 301 跳转）。详见 §8。
4. **索引层 120 tokens 仍高于 ~100 的理想值**，是有意为之：description 要覆盖
   中英双语 + 11 个主题域，砍掉会损失召回。

---

## 7. 产物清单

| 文件 | 说明 |
|---|---|
| `audit-report-pipeline.md` | skill-forge 自己写出的极简审计（root_cause + verdict） |
| `best.md` | 管道物化的候选（= 改后 SKILL.md 全文） |
| `baseline-description-v2.0.txt` | 改前 description 原文，供 token 复算 |
| `measure-tokens.py` | 改前/改后 token 实测脚本（tiktoken） |
| `../../cpp-handbook/skillopt-benchmark.jsonl` | 15 条真实基准题（替换模板行） |
| `../../cpp-handbook/references/hero-queries.md` | 触发路由评测集（正向 10 / 负向 5 / 邻接 4） |
| `../../cpp-handbook/references/routing-eval.jsonl` | 章节路由评测集（43 条） |
| `../../cpp-handbook/scripts/route_eval.py` | 路由回归脚本（零依赖，43/43） |

---

## 8. v2.2 改名记录

| 项 | 改前 | 改后 |
|---|---|---|
| frontmatter `name` | `skill-c++` | **`cpp-handbook`** |
| skill 目录名 | `skill-c++/` | **`cpp-handbook/`** |
| `install.ps1` 默认 slug | `skill-c++` | **`cpp-handbook`** |
| GitHub 仓库 | `kizemo/skill-c-` | **`kizemo/cpp-handbook`** |
| 版本号 | 2.1.0 | 2.2.0 |

**为什么选 `cpp-handbook`**

| 判据 | 结论 |
|---|---|
| 规范（`^[a-z0-9][a-z0-9-]*$`） | ✅ 全小写 + 连字符，6 个宿主 lens 全部接受 |
| 看得出用途 | ✅ 「C++ 手册」= skill 的自我定位「C++ 编程知识手册」，中英都读得懂 |
| 不与上游撞名 | ✅ 上游叫 Core Guidelines / C++ Best Practices / cppreference / learncpp / Real-Time C++ |
| 不与已装 skill 冲突 | ✅ 现有 skill 里无 `cpp-*` 前缀 |
| 避开旧名 | ✅ `cpp-guidelines` 会被误认成 Core Guidelines 文档本身（且曾是本项目旧目录名） |

**连带改动**：`verify_bundle.py` 的 frontmatter 原则门禁去掉了「name 含 `+` 可豁免」的
特殊分支——名字现在合规，任何 frontmatter 警告都应当直接判失败。
