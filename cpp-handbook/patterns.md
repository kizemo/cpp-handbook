# 手法与惯用法

> 具体可执行的做法。什么时候用、怎么做、代价是什么。

## RAII 资源句柄
**When to use**：任何需要"获取—释放"成对出现的资源——内存、文件句柄、锁、socket、事务。
**How**：把资源包进一个类，构造时获取、析构时释放；获取失败时抛异常或返回错误，
析构函数必须 `noexcept`。
**Trade-offs**：多一层包装；但异常路径、提前 return、正常结束三条路径统一由析构兜住。

## Rule of Zero
**When to use**：默认选它。
**How**：所有成员自己管资源（用 `std::vector`/`std::string`/`std::unique_ptr`），
你自己**不写**任何拷贝/移动/析构函数。
**Trade-offs**：几乎无代价（一个指针的额外间接），换来"不会写错特殊成员函数"。

## Rule of Five（退化路径）
**When to use**：确实需要自定义资源管理行为时。
**How**：析构、拷贝构造、拷贝赋值、移动构造、移动赋值**五个一起写**；
不可拷贝就把拷贝构造**和**拷贝赋值**都** `= delete`（只写一个，拷贝赋值不会被自动删除，C.21）；
移动操作必须 `noexcept`。
**Trade-offs**：代码量大、易错；能用 Rule of Zero 就别用。

## pImpl（指针实现）
**When to use**：需要把 ABI 稳定下来，或想把编译依赖挡在实现文件里。
**How**：`class X { struct Impl; std::unique_ptr<Impl> impl_; };`，`Impl` 定义放 .cpp。
**Trade-offs**：多一次间接、额外的分配；换来 ABI 稳定与编译加速。

## 委托构造
**When to use**：多个构造函数有共同初始化逻辑。
**How**：`X(int a) : X(a, 0) {}` 委托到主构造函数（C.51）。
**Trade-offs**：无；比复制粘贴初始化列表可靠。

## 删除拷贝 + 自定义移动
**When to use**：类型不可拷贝但可移动（句柄类型、独占资源类型）。
**How**：`X(const X&) = delete; X& operator=(const X&) = delete; X(X&&) noexcept = default;`
**Trade-offs**：需要显式想清楚"拷贝会发生吗"。

## `erase-remove` 惯用法
**When to use**：按条件删除容器元素。
**How**：`v.erase(std::remove(v.begin(), v.end(), pred), v.end());`
**Trade-offs**：两次遍历；`std::remove` **只移动不删除**，漏掉 `erase` 就是 bug。

## 字符串视图
**When to use**：只读、不需要拥有、生命周期明确短于被引用对象时。
**How**：`std::string_view sv{str};` 传参用 `std::string_view` 避免拷贝。
**Trade-offs**：**不拥有**——被引用的 `std::string` 析构后 view 就悬垂；
不要把 `string_view` 存成成员，除非同时保证底层对象活得久。

## 作用域锁 / 多锁一次获取
**When to use**：任何加锁场景。
**How**：单锁用 `std::lock_guard`；多锁用 `std::scoped_lock`（内部用死锁避免算法，CP.21）；
需要手动 unlock 时用 `std::unique_lock` 并给它起名字（CP.44）。
**Trade-offs**：`unique_lock` 比 `lock_guard` 重，但可控。

## `call_once` 初始化
**When to use**：多线程共享的一次性初始化。
**How**：`std::call_once(flag, [&]{ init(); });`
**Trade-offs**：比双检锁简单可靠；别自己写双检锁（CP.110/CP.111）。

## 条件变量等待
**When to use**：等待某个条件成立，而不是"等一段时间"。
**How**：`unique_lock` + `cv.wait(lock, [&]{ return predicate; });`
**Trade-offs**：必须用带谓词的 `wait`，否则会虚假唤醒；不要用 `wait_for` 代替条件判断。

## 线程池
**When to use**：任务粒度小、创建线程成本占主导时。
**How**：固定 N 个 worker + 任务队列 + 条件变量；提交任务时用 `std::future` 拿结果（CP.60）。
**Trade-offs**：需要自己处理异常传播与优雅退出；`std::async` 简单但每个任务一个线程。

## 范围算法（C++20 Ranges）
**When to use**：新代码想要更安全的算法接口。
**How**：`std::ranges::find(v, x)`、`std::ranges::sort(v)`；配合管道 `| std::views::transform(...)`。
**Trade-offs**：C++20 起才有；投影参数比普通算法复杂。

## 概念约束（`requires`）
**When to use**：模板参数需要编译期约束。
**How**：`template <std::integral T> void f(T x);`，或 `requires std::same_as<T, int>`；
同一类型约束用简写 `std::same_as<T>`（T.13）。
**Trade-offs**：C++20 起才有；比 SFINAE 直白，但错误信息依赖编译器质量。

## 编译期计算
**When to use**：结果固定、计算量不大。
**How**：`constexpr` 函数 + `consteval`（强制编译期求值）；`std::array` 代替 `std::vector`。
**Trade-offs**：编译期变长需要 C++20 的 `std::vector`  constexpr 支持。

## 预期值（`std::expected`）
**When to use**：失败是类型的一部分，调用方必须处理。
**How**：`std::expected<int, std::error_code> r = do_work(); if (!r) { /* r.error() */ }`
**Trade-offs**：C++23 才有；比异常更显式，但会传染到整个调用链。

## 终结动作（`final_action`）
**When to use**：没有合适的 RAII 资源句柄，但确实需要清理。
**How**：`std::scope_exit`（C++23）或 `final_action` 风格的 guard 对象。
**Trade-offs**：能兜底，但不如真正的资源句柄——优先造一个资源句柄。

## 编译器 + Sanitizer 门禁
**When to use**：每个项目的 CI 里。
**How**：编译加 `-Wall -Wextra -Wpedantic -Werror`；测试跑
`-fsanitize=address,undefined`（内存与 UB），并发部分跑 `-fsanitize=thread`。
**Trade-offs**：编译变慢、内存占用上升；换来的 bug 提前暴露值这个价。

## 静态初始化顺序（函数内静态）
**When to use**：有动态初始化的全局对象。
**How**：把全局对象包进函数里：`const Widget& w() { static const Widget x; return x; }`
（局部静态自 C++11 起线程安全）。
**Trade-offs**：多一次调用；换来跨翻译单元顺序问题的消失。
