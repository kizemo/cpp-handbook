# Chapter 14: 来源台账（Sources）

## Core Idea
这 20 个来源不是"资料堆"，而是一条**分层的取证链**——**先查权威原文（规则/标准），
再查工程实践，最后才查风格偏好**。选源的顺序比来源的数量重要得多。

## Frameworks Introduced
- **三级取证（Rule → Practice → Style）**：回答"这段代码该怎么改"时，
  先查规则原文（`01`），再查工程实践（`03`），最后才查风格指南（`09`/`10`）。
  **When to use**：任何规范类问题。**How**：规则定"对错"，实践定"取舍"，风格只定"长相"。
  三者冲突时**规则优先**——风格指南可以让位于正确性。
- **按问题类型选源，不按主题浏览**：先确定问题的形状（要规则原文？要 API 语义？
  要工程组织？），再决定翻哪个目录。
  **When to use**：想查资料却不知道从哪下手时。**How**：用下面的"按用途选源"表反查。
- **快照可复现（Reproducible snapshot）**：每个来源都记录了实际下载到本地的 commit。
  **When to use**：需要引用出处、或上游更新后要复现旧结论时。
  **How**：重跑 `_meta/fetch.ps1` 刷新快照；引用时带上 commit。
- **许可先于内容**：每个目录的 `LICENSE` 随仓库一起下载。
  **When to use**：打算在商业项目里引用其中内容时。**How**：先读许可，再决定怎么用。

## Key Concepts
- **浅克隆快照（Shallow snapshot）**：`git clone --depth 1`，只取最新一次提交
- **权威层级（Authority tier）**：ISO 官方指南 > 工程实践 > 个人教程 > 风格偏好
- **★ 星数**：社区关注度，是**流行度**指标，不是**正确性**指标
- **元文件（Metafile）**：`README.md` / `index.md` / `log.md` / `schema.md` / `RESOLVER.md`
- **重命名映射（Rename map）**：原始名 → 现名的对照表，公开记录在 `_meta/renames.tsv`
- **一句话定位**：每个来源"它到底解决什么问题"的压缩说明

## Mental Models
- **把它当图书馆，不当搜索引擎**：图书馆有分类、有索引、有原文出处；
  你不会因为"书多"就相信每一本，但你相信"分类 + 索引 + 出处"这套机制。
  **因此：先定位到正确的架位，再取书**。
- **★ 不是权威度**：Google 风格指南 39.7k 星，ISO 草案只有 233 星——
  但当"标准怎么规定的"这个问题出现时，答案是 ISO 草案，不是 Google 风格。
- **中文二手 vs 英文一手**：中文全译本和教程读起来快，但**裁决争议时要看英文原文**。

## Anti-patterns
- **把 star 数当权威度**：star 衡量关注度。一个被广泛引用但过时的教程照样 star 很高。
- **只读二手不查一手**：中文译本可能滞后于上游；与标准条文冲突时以英文原文为准。
- **不看许可就抄进商业项目**：本库 20 个来源的许可各不相同
  （CC BY / MIT / Unlicense / BSL-1.0 / GPL-3.0 / 若干未声明）。
- **把 awesome 索引当知识源**：`15`/`16`/`17` 是**资源目录**——它们指向知识，不包含知识。

## Code Examples
`05-modern-cpp-course` 与 `11-real-time-cpp` 等目录含 PDF/图片等二进制资源，
它们留在本地磁盘上但**不进 git、也不会被检索系统摄入**——需要看原件时直接打开本地文件。
这类资源的处理方式说明了一件事：**内容分层是按"可检索性"划的，不是按"重要性"划的**。

## Reference Tables

**20 个来源总览**

| # | 目录 | 上游 | ★ | 许可 | 一句话定位 |
|---|---|---|---|---|---|
| 01 | `01-core-guidelines` | isocpp/CppCoreGuidelines | 45.4k | CC BY 4.0 / MIT | **ISO C++ WG21 官方指南**，约 1400 条规则，每条带正反例 |
| 02 | `02-core-guidelines-zh` | lynnboy/CppCoreGuidelines-zh-CN | 2.6k | 同上 | 01 的**简体中文全译本** |
| 03 | `03-best-practices` | cpp-best-practices/cppbestpractices | 8.8k | CC BY 3.0 | C.42 体系"最佳实践"，按安全性/可维护性/可移植性/线程安全/性能/正确性分章 |
| 04 | `04-modern-cpp-tutorial` | changkun/modern-cpp-tutorial | 25.9k | MIT | 现代 C++ 教程，**中英双语**章节 + 配套代码 |
| 05 | `05-modern-cpp-course` | federico-busato/Modern-CPP-Programming | 16.2k | CC BY-SA 4.0 | 系统化课程讲义（30 讲 PDF）+ 配套源码 |
| 06 | `06-modern-cpp-features` | AnthonyCalandra/modern-cpp-features | 21.9k | MIT | **现代 C++ 特性速查表**，C++11→C++26 |
| 07 | `07-algorithms` | TheAlgorithms/C-Plus-Plus | 34.8k | MIT | **算法实现大全**，每个算法带示例与单测 |
| 08 | `08-leetcode-cases` | kamyu104/LeetCode-Solutions | 6.0k | MIT | **4000+ 道 LeetCode 题的 C++ 解法** |
| 09 | `09-google-style` | google/styleguide | 39.7k | CC BY 3.0 | **Google C++ 风格指南** |
| 10 | `10-google-style-zh` | shendeguize/GoogleCppStyleGuideCN | 14 | — | Google 风格指南**中文版** |
| 11 | `11-real-time-cpp` | ckormanyos/real-time-cpp | 817 | BSL-1.0 | 《Real-Time C++》书稿 + **可运行示例工程** |
| 12 | `12-iso-draft` | cplusplus/draft | 233 | — | **ISO C++ 标准工作稿本体**（LaTeX 源 + Markdown 转换版） |
| 13 | `13-cmake-best-practices` | cpp-best-practices/cmake_template | 1.8k | Unlicense | **CMake 最佳实践**模板与规则 |
| 14 | `14-modern-cpp-starter` | TheLartians/ModernCppStarter | 5.4k | Unlicense | 现代 C++ 工程脚手架（CMake + CI + clang-format + 覆盖率） |
| 15 | `15-awesome-cpp` | fffaraz/awesome-cpp | 73.9k | MIT | **C++ 生态总索引** |
| 16 | `16-awesome-modern-cpp` | rigtorp/awesome-modern-cpp | 13.2k | — | 现代 C++ 专用资源索引 |
| 17 | `17-awesome-perf-cpp` | fenbf/AwesomePerfCpp | 2.6k | — | **性能优化**专题资源 |
| 18 | `18-cppreference-doc` | p12tic/cppreference-doc | 478 | GPL-3.0 / CC BY-SA 3.0 | cppreference 的 **84 个标准库头文件接口说明** |
| 19 | `19-learncpp-cn` | hanxiaomax/Learncpp_CN | 167 | MIT | **learncpp.com 简体中文全译**（667 篇） |
| 20 | `20-cpp-notes-cn` | hengqiali/AwesomeCpp | 2.0k | — | 中文 C++ 学习笔记 + **面试知识点** |

**按用途选源**

| 我要解决的问题 | 先看 |
|---|---|
| "这段代码该怎么写才规范" | `01`（规则）→ `03`（实践）→ `09`/`10`（风格） |
| "C++20/23 有哪些新特性" | `06`（速查）→ `04`（教程 10/11 章）→ `05`（课程） |
| "这个算法怎么实现" | `07`（实现+单测）→ `08`（题目变体） |
| "标准是怎么规定的" | `12`（标准原文）→ `18`（头文件接口） |
| "从零开始学" | `19`（中文全译）→ `04`（现代 C++） |
| "怎么搭工程" | `13`（CMake）→ `14`（脚手架）→ `03`（可维护性） |
| "怎么跑得更快" | `17`（资源）→ `03` 第 8 章（性能） |
| "还有哪些库/工具值得知道" | `15` → `16` |
| "面试怎么答" | `20`（笔记+面试点）→ `01`（规则原文） |

**本地改动的唯一结构性部分：重命名**（不删内容、不改内容）

| 原始 | 现名 |
|---|---|
| `01-core-guidelines/README.md` | `01-core-guidelines/overview.md` |
| `06-modern-cpp-features/README.md` | `06-modern-cpp-features/modern-cpp-features-cheatsheet.md` |
| `07-algorithms/README.md` | `07-algorithms/overview.md` |
| `08-leetcode-cases/README.md` | `08-leetcode-cases/overview.md` |
| （其余 17 处见 `_meta/renames.tsv`） | |

原因：检索系统把 `README.md` / `index.md` / `log.md` / `schema.md` / `RESOLVER.md`
视为"元文件"而跳过导入。官方建议就是"重命名它"——不删内容，映射公开留档。

## Worked Example
**一次完整取证：「这个 `shared_ptr` 循环引用该怎么改？」**

1. **先定问题形状**：这是"所有权/生命周期"问题 → 先查规则原文，不是先查风格指南。
2. **查规则（`01`）**：搜 `R.24` —— "Use `std::weak_ptr` to break cycles of `shared_ptr`s"。
   规则原文带正反例，反例正好就是这个 bug 形态。
3. **查主题层（Ch01）**：中文主题页把这条落到"父子互指时哪条边该是 `weak_ptr`"，
   并给出可编译的 `weak_ptr::lock()` 解法。
4. **查工程实践（`03` 第 4 章 "Considering Safety"）**：看实践里怎么处理共享所有权，
   补充"默认用 `unique_ptr` + 明确管理者，共享是例外"这条工程建议。
5. **最后才看风格（`09`）**：只确认命名与写法风格，不影响方案。
6. **核对许可**：若要把示例抄进商业项目，先看 `01` 的 `LICENSE`（CC BY 4.0 / MIT），
   满足署名条件即可。

整条链走完，结论有出处、有反例、有工程取舍、许可清楚——
而不是"凭印象说用 `weak_ptr`"。

## Key Takeaways
1. 选源顺序：规则原文 → 工程实践 → 风格偏好。风格永远让位于正确性。
2. ★ 是流行度不是权威度；ISO 草案只有 233 星，却是"标准怎么规定"的唯一答案。
3. 每个来源都记了快照 commit，引用时带上，出处可复现。
4. 20 个来源许可各不相同，抄进商业项目前先读 `LICENSE`。
5. `15`/`16`/`17` 是资源目录（指向知识），不是知识本身。
6. 争议以英文原文为准；中文译本和教程是加速器，不是裁决者。
7. 对上游只做过重命名，映射公开留档，没有静默删改。

## Connects To
- **Ch15**: 知识地图——来源在三层结构中的位置
- **Ch09**: 工程实践——`13`/`14` 这两个来源的直接用途
- **Ch01**: 所有权与生命周期——`R.24` 这条规则的完整落地
- **Ch12**: 案例索引——`07`/`08` 怎么用
