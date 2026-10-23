# 十条心智模型（核心框架详解）

> **这是 L1 层**：只有当问题是"整体该怎么写 / 这段代码该怎么组织"时才读它。
> 具体专题问题请直接跳到 `chapters/chNN-*.md` 对应的一章，不要通读全库。
> 每节末尾的"规则号"可用 `scripts/kb_lookup.py "<规则号>"` 回知识库查原文。

---

## 1. 单一主人原则（Single Owner）

C++ 里每块内存有且只有一个明确的"主人"，主人的职责是在自己活着的时候释放它。
指针/引用是**借用**，不延长生命周期；智能指针是**拥有**。

- 主人默认是 `unique_ptr`，确需共享才用 `shared_ptr`，成环用 `weak_ptr` 破
- 借用在签名上用 `T&`/`T*` 表达，**不要**用智能指针表达借用
- **最优先的答案是 Rule of Zero**：让成员类型自己管资源，你什么都不写

> 提问的第一句："这块内存谁负责释放？" 答不出来就先别写。

规则号：`R.20` `R.21` `R.24` `F.7` `F.43`
相关章节：[ch01 所有权与生命周期](../chapters/ch01-ownership-and-lifetime.md) · [ch02 移动语义](../chapters/ch02-move-semantics.md)

---

## 2. RAII 是默认解法，不是"高级技巧"

构造时获取资源、析构时释放资源——对**任何**资源成立：内存、文件句柄、锁、socket、事务。
栈展开保证异常路径上已构造对象的析构照常执行，所以 RAII 天然覆盖
"正常结束 / 提前 return / 抛异常"三条路径。

- 不用裸 `new`/`delete`，用 `make_unique`/`make_shared`（异常安全）
- 移动操作必须标 `noexcept`，否则 `std::vector` 扩容会退化成深拷贝
- 不返回局部对象的指针或引用——按值返回，交给 RVO/移动

规则号：`R.11` `R.20` `F.43`
相关章节：[ch01](../chapters/ch01-ownership-and-lifetime.md) · [ch06 错误处理](../chapters/ch06-error-handling.md)

---

## 3. 证明优于假设（并发）

并发的难点不是"怎么加锁"，而是"**怎么证明没有数据竞争**"。

- 默认单线程；并发是需要明确论证的优化手段，不是起点
- 考虑顺序：更快的算法/数据结构 → 批处理/缓存/惰性求值 → 单线程异步 → 多线程
- 锁与它保护的数据放在一起定义；多锁用 `std::scoped_lock`
- `volatile` 只用于访问非 C++ 内存，**不做同步**；用 TSan 验证

规则号：`CP.8` `CP.9` `CP.21` `CP.50` `Per.1` `Per.2`
相关章节：[ch05 并发编程](../chapters/ch05-concurrency.md) · [ch10 工具链与调试](../chapters/ch10-toolchain-and-debugging.md)

---

## 4. 先测量，再优化

没有 profiler 数据支撑的"优化"，90% 是把代码改慢而不是改快。

- 没有理由不优化，不提前优化，不优化非关键路径
- 优先级：算法复杂度 → 内存布局/分配 → 常数因子
- 热点路径避免分配；能编译期算就编译期算

规则号：`Per.1` `Per.2` `Per.3` `Per.11` `Per.15`
相关章节：[ch07 性能优化](../chapters/ch07-performance.md)

---

## 5. 工具优先于记忆

**能被工具检出的坑，都不该靠人肉记。** C++ 的坑集中在三类：未定义行为（UB）、
所有权错乱、API 误用——每一类都有对应的编译器警告或 Sanitizer 报告。

- 编译期：`-Wall -Wextra -Wpedantic -Werror`；内存与 UB：ASan + UBSan；竞争：TSan
- **UB 不是"跑起来没崩就没问题"**——越界读可能"看起来是对的"，换编译器/优化级别就崩
- 定位顺序：工具 → 调试器 → 核心转储，**不是加 `printf`**

规则号：`CP.9`
相关章节：[ch10 工具链与调试](../chapters/ch10-toolchain-and-debugging.md) · [ch11 陷阱与反模式](../chapters/ch11-pitfalls-and-antipatterns.md)

---

## 6. 在接口边界选一种错误机制，然后一致到底

C++ 有三种错误处理方式：异常、错误码、预期值（`std::expected`）。

- 关键是**在接口边界就选定一种并保持一致**，而不是在实现里到处混用
- 异常只用于表示"做不了"，不是流程控制
- 析构函数绝不抛异常；`noexcept` 要标注**真实契约**，不是"我猜它不会抛"
- 异常路径上的资源释放靠 RAII；没有合适资源句柄时用 `final_action`

规则号：`E.1` `E.2` `E.3` `E.6`
相关章节：[ch06 错误处理](../chapters/ch06-error-handling.md) · [ch08 现代 C++ 特性](../chapters/ch08-modern-cpp-features.md)

---

## 7. 算法优先于手写循环

标准库算法是"经得起所有边界条件检验"的实现。

- 容器选对了，代码就快一半：默认 `vector`，有序用 `map`/`set`，哈希用 `unordered_*`
- `std::remove` **不删除元素**，只做移动——必须 `erase(std::remove(...), end())`
- 迭代器失效规则要背：`vector` 扩容、`map`/`set` 删除、`unordered_*` rehash
- C++20 Ranges 提供更安全的算法接口；`string_view` 是非拥有的视图，别让它悬垂

相关章节：[ch04 STL 容器与算法](../chapters/ch04-stl-containers-algorithms.md) · [ch11 陷阱与反模式](../chapters/ch11-pitfalls-and-antipatterns.md)

---

## 8. 编译期约束优于运行期检查

模板是编译期的代码生成器，Concepts 是给模板参数加的编译期约束。

- C++20 之前靠 SFINAE 表达约束，C++20 之后用 `requires` 子句直接说清楚
- 优先用标准概念（`std::integral`、`std::same_as`）
- 同一类型约束用简写 `std::same_as<T>` 而不是展开

规则号：`T.11` `T.13`
相关章节：[ch03 模板与 Concepts](../chapters/ch03-templates-and-concepts.md)

---

## 9. 让 bug 在提交前暴露

现代 C++ 工程的标配是 **CMake + 单元测试 + 静态分析 + Sanitizer + CI**。
核心目标是让 bug 在**提交前**暴露，而不是在生产环境暴露。
规范类知识（命名、包含顺序）按项目约定走，别拿个人偏好当缺陷。

相关章节：[ch09 工程实践](../chapters/ch09-project-practices.md) · [ch10 工具链与调试](../chapters/ch10-toolchain-and-debugging.md)

---

## 10. 规则号要能追溯

引用 C++ Core Guidelines 时给出规则号，人才能核对。`scripts/rule_lint.py` 用 500 条真源规则
做白名单，能抓「编号不存在」和「编号存在但用错章节」两类错。

前缀含义：并发 `CP.*`、性能 `Per.*`、所有权 `R.*`、宏/语句 `ES.*`、类 `C.*`、
函数 `F.*`、错误处理 `E.*`、模板 `T.*`。

> 知识库首版曾有 **25 处错引**，肉眼无一发现——所以这件事必须由脚本做。

相关章节：[ch15 知识地图与库结构](../chapters/ch15-knowledge-map.md)
