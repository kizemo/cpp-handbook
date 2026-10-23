---
name: cpp-handbook
description: >-
  Use when writing, reviewing, refactoring or debugging C++ (C++11–C++26) code:
  ownership and lifetime, move semantics, templates and Concepts, STL containers
  and algorithms, concurrency and data races, error handling, performance,
  modern C++ features, CMake/CI practice, Sanitizers, and Core Guidelines rule
  lookup. 写 C++ 代码、做 C++ 评审、排查崩溃/数据竞争/内存错误、查规则原文时使用。
argument-hint: "[topic | ch01-ch15 | 规则号]"
triggers:
  - "帮我 review 这段 C++ 代码"
  - "shared_ptr 循环引用怎么破"
  - "这段代码有没有数据竞争"
  - "ASan 报的 heap-use-after-free 怎么查"
  - "vector 扩容会不会让迭代器失效"
  - "CMake 工程怎么组织测试和 CI"
  - "Core Guidelines 里哪条规则说别用裸 new"
mutating: false
brain_first: exempt
when_to_use: >-
  只覆盖通用 C++ 知识；项目私有约定以该项目自己的 AGENTS.md 为准。
version: 2.2.0
---

# C++ 编程知识手册

20 个权威来源（ISO C++ WG21 Core Guidelines、Google Style、C++ Best Practices、
cppreference、learncpp、Real-Time C++ 等）的消化层：**15 章 + 速查 + 可执行校验**。

**分工**：查"该怎么做"看本文件与章节；查"条文 / 精确措辞 / API 语义"回知识库。

## 渐进式披露：四层，别一次性读完

| 层 | 何时加载 | 内容 |
|---|---|---|
| L0 | 每次触发 | 本文件：路由 + 铁律 + 红旗 |
| L1 | 问"整体该怎么写" | 10 条心智模型详解 → `references/core-framework.md` |
| L2 | 问具体问题 | 单章 → `chapters/chNN-*.md` |
| L3 | 要条文 / API 语义 | 知识库原文 → `scripts/kb_lookup.py` |

**先定位到一章，只读那一章**；需要条文再跳 L3。不要一次读完 L1 + L2 + L3。

## 检索路由

- **要条文 / 精确措辞 / API 语义** → `scripts/kb_lookup.py "<关键词>"`（本地全文检索，不占脑锁）
- **要核对规则号** → `scripts/rule_lint.py <路径>`（500 条真源白名单）
- **要具体做法** → 查下面的章节索引，**只读命中的那一章**
- **要决策表 / 惯用法 / 术语** → `cheatsheet.md` · `patterns.md` · `glossary.md`
- **项目私有约定** → 项目自己的 `AGENTS.md`，本 skill 只管通用 C++

路由评测集见 `references/hero-queries.md`；改 `description` / `triggers` 后重跑
`scripts/route_eval.py`，索引缺词会当场报出来。

## 章节索引

| 章 | 标题 | 触发词（命中任一即读该章） |
|---|---|---|
| [ch01](chapters/ch01-ownership-and-lifetime.md) | 所有权与生命周期 | shared_ptr, unique_ptr, weak_ptr, 循环引用, 悬垂, 悬空指针, 生命周期, 智能指针, Rule of Zero, Rule of Five, 所有权, 析构函数 |
| [ch02](chapters/ch02-move-semantics.md) | 移动语义与完美转发 | std::move, std::forward, move语义, 移动语义, 完美转发, noexcept, 拷贝消除, 值类别, 右值, 引用折叠 |
| [ch03](chapters/ch03-templates-and-concepts.md) | 模板与 Concepts | 模板, template, SFINAE, Concepts, requires, 约束, 变参模板, CRTP, 概念, 模板特化 |
| [ch04](chapters/ch04-stl-containers-algorithms.md) | STL 容器与算法 | vector, map, unordered_map, 容器选型, 迭代器失效, erase-remove, std::remove, string_view, 算法, ranges, 迭代器, 容器, list, deque, queue |
| [ch05](chapters/ch05-concurrency.md) | 并发编程 | 数据竞争, data race, 线程, mutex, 互斥锁, 原子, 内存序, 条件变量, 线程池, 并发, 锁, thread, atomic |
| [ch06](chapters/ch06-error-handling.md) | 错误处理 | 异常, exception, 错误码, std::expected, 异常安全, try-catch, 错误处理, noexcept契约, 预期值 |
| [ch07](chapters/ch07-performance.md) | 性能优化 | 性能, 优化, benchmark, 基准测试, 缓存, 复杂度, 分配, 热点, profiling, profiler, 性能优化 |
| [ch08](chapters/ch08-modern-cpp-features.md) | 现代 C++ 特性全景 | C++11, C++14, C++17, C++20, C++23, C++26, 现代 C++, ranges, jthread, 模块, 结构化绑定, 特性, 版本选型 |
| [ch09](chapters/ch09-project-practices.md) | 工程实践 | CMake, CI, 单元测试, 测试, clang-format, 警告即错误, 工程实践, 依赖管理, 项目目录结构 |
| [ch10](chapters/ch10-toolchain-and-debugging.md) | 工具链与调试 | gdb, lldb, 调试器, sanitizer, ASan, UBSan, TSan, core dump, 编译警告, 工具链, perf, valgrind, 崩溃, 内存泄漏 |
| [ch11](chapters/ch11-pitfalls-and-antipatterns.md) | 陷阱与反模式 | 陷阱, 反模式, undefined behavior, UB, 未定义行为, 宏, 虚析构, virtual destructor, 溢出, API误用, 坑, 常见错误 |
| [ch12](chapters/ch12-cases.md) | 案例索引 | 算法案例, leetcode, 题解, 案例, 例题, 练习题 |
| [ch13](chapters/ch13-learning-path.md) | 学习路线 | 学习路线, 学习路径, 进阶, 入门, 怎么学, 路线图, 书 |
| [ch14](chapters/ch14-sources.md) | 来源台账 | 来源, 台账, 许可, license, 版权, 出处, 作者, 来源清单 |
| [ch15](chapters/ch15-knowledge-map.md) | 知识地图与库结构 | 知识地图, 库结构, 双链, knowledge map, 知识库结构, 目录结构 |

## 七条铁律（L0 摘要）

1. **单一主人**：每块内存只有一个主人；指针/引用是借用，智能指针是拥有（R.20/R.21/R.24）。
2. **RAII + Rule of Zero**：优先让成员类型自己管资源，你什么都不写（R.11）。
3. **移动必须 `noexcept`**：否则 `std::vector` 扩容退化成深拷贝。
4. **并发要证明，不要假设**：默认单线程；`volatile` 不做同步（CP.8）。
5. **先测量再优化**：优先级是算法复杂度 → 内存布局 → 常数因子（Per.3）。
6. **工具优先于记忆**：能被 Sanitizer / 编译器警告检出的坑，别靠人肉记（CP.9）。
7. **规则号要能追溯**：给编号才能核对，`rule_lint.py` 用 500 条真源白名单查。

十条完整版（含"为什么 / 怎么做 / 相关章节"）见 `references/core-framework.md`。

## Red Flags 与陷阱清单

- **"跑起来没崩"不等于没有 UB**：越界读可能看起来是对的，换编译器或优化级别就崩 → 上 ASan/UBSan。
- **凭记忆写规则号**：编号可能不存在，或用错章节（并发是 `CP.*` 不是 `Con.*`）→ `rule_lint.py`。
- **`std::remove` 不删除元素**，只做移动 → 必须 `erase(std::remove(...), end())`。
- **在析构函数里抛异常** → `std::terminate`，直接终止进程。
- **多锁手动 `lock()` / `unlock()`** → 死锁风险，用 `std::scoped_lock`（CP.21）。
- **把 `shared_ptr` 当借用传参** → 签名上应当是 `T&` / `T*`（F.7）。
- **规范类偏好被当成缺陷**：命名、包含顺序按项目约定走，别拿个人偏好当 bug。
- **"这条规则适用到我项目吗"是工程判断**，不是知识问题 → 不确定就说不确定。

## 可执行校验（不要靠自觉）

```powershell
python scripts/kb_lookup.py "ownership shared_ptr cycle" --top 6   # 查原文
python scripts/rule_lint.py src include docs                        # 抓错规则号
python scripts/verify_bundle.py                                    # 索引陈旧 / 指针失效
python scripts/route_eval.py                                        # 章节索引路由回归
```

配套：`cheatsheet.md` 决策表 · `patterns.md` 惯用法 · `glossary.md` 术语 ·
`references/checklists.md` 自检清单 · `references/rule-index.md` 500 条规则号索引 ·
`references/source-map.md` 问题类型 → 知识库位置。

## 边界与限制

- 覆盖**通用 C++ 知识**；项目特有约定以项目的 `AGENTS.md` 为准，冲突时按项目走并指出冲突。
- 章节是**提炼**不是原文；精确措辞、API 语义、标准条文 → `kb_lookup.py` 回知识库。
- 工具链内容以 GCC/Clang/MSVC 为主，其它编译器可能有差异。
- 未部署知识库时，章节、规则索引、速查表**照常可用**，只有原文检索失效。
