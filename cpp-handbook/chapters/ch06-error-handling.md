# Chapter 6: 错误处理（Error Handling）

## Core Idea

错误处理的核心不是"选异常还是选错误码"的二选一，而是**在接口边界先把失败定性，再让全库只用一种传递方式**。先问"这是编程错误还是运行时失败"，再选机制；机制在边界定下后，内部必须一致到底（E.1、E.4）。

## Frameworks Introduced

- **三机制分工（Exception / error_code / expected）**：异常管罕见且无法就地处理的失败，`std::error_code` 管预期内失败，`std::expected` 管"值或错误一起传"。
  - When to use: 设计会失败的公开接口。
  - How: 内部用异常，边界用 `expected` / `error_code`（E.2、E.3）；禁用异常时系统化地用错误码（E.27）。
- **编程错误 / 运行时失败二分（Programming error vs runtime failure）**：先定性，再决定要不要处理。
  - When to use: 遇到任何一条错误分支。
  - How: 编程错误走断言，运行时失败用 `expected` / `error_code`（E.7、E.26、I.6）；构造函数建不起不变式就抛异常（E.5、C.42）。
- **异常安全三级保证（Basic / Strong / Nothrow）**：抛出后对象处于什么状态，属于函数契约。
  - When to use: 任何会改状态的操作。
  - How: 默认真保基本保证，要回滚就做强保证，确定不抛的标 `noexcept`（E.12、E.16、C.37）。
- **先算后提交（commit-after-compute）**：强保证的标准写法。
  - When to use: 需要"要么全做完，要么没发生"的操作。
  - How: 可能失败的工作先在临时对象上做完再提交；无资源句柄时用 `final_action` 清理（E.6、E.19、P.8）。
- **边界翻译（boundary translation）**：把内部异常在库边界翻译成对外的错误表达。
  - When to use: 库要给 C ABI、非 C++ 调用方或要 `error_code` 的调用方用。
  - How: 内部抛具体异常类型，边界捕获住转成错误码，对外只暴露错误码（E.14、E.15、E.31）；跨编译器 ABI 用 C 风格子集（I.26）。
- **`noexcept` 作为契约（noexcept as a contract）**：写给调用者的前提，不是优化开关。
  - When to use: 声明"确定不会抛"或"抛了也救不了"的函数。
  - How: 析构、释放、`swap`、移动一律标 `noexcept`，拿不准就不标（F.6、E.12、C.66、C.85）。

## Key Concepts

- **编程错误（programming error）**：程序自身的缺陷，调用者无法合理恢复；用断言表达。
- **运行时失败（runtime failure）**：外部世界导致（文件不存在、超时），调用者能决定重试还是报错。
- **异常安全三级保证（exception safety guarantees）**：基本保证（有效、无泄漏）、强保证（状态与调用前完全相同）、不抛保证（`noexcept`）（E.16、C.36、C.37）。
- **异常规格（exception specification）**：`throw(std::runtime_error)` 自 C++17 起弃用；现代唯一的异常规格是 `noexcept`（E.30）。
- **按值抛出、按引用捕获（throw by value, catch by reference）**：避免对象切片，只有按基类引用捕获才接得住派生类（E.15）。
- **错误码（error code）**：`std::error_code` + `std::errc`，无异常机制、可与返回值共存、适合 C 风格 ABI。
- **预期值（`std::expected`，C++23）**：把"值或错误"编码进返回类型，不处理就编译不过。
- **`catch` 子句顺序（catch-clause ordering）**：先具体后一般，`catch (...)` 永远最后（E.31）。
- **断言（assert）**：表达"这不该发生"的内部检查，`NDEBUG` 下被消除，不是错误处理机制。

## Mental Models

- 把异常当"跳到最外层的 `goto`"，不是"打印一行错误日志"：能往上传就别自己捕获（E.17、E.18）。
- 把 `noexcept` 当"给调用者的契约签名"：它说的是"我抛了，你也救不了"，宁可漏标不要错标（F.6、E.12）。
- 把 `std::expected` 当"把失败焊进类型里"：类型系统强迫你在编译期面对"可能失败"。
- 把 `assert` 当"给开发者看的内部检查"，不是错误处理：Release 下 `NDEBUG` 会让它消失。

## Anti-patterns

- **析构函数抛异常**：栈展开期间再抛 → `std::terminate`（E.16、C.37）。
- **`catch (...)` 到处吞异常**：具体异常退化成"未知错误"，线索全丢（E.17、E.31）。
- **错误码不检查**：`f.open(path, ec)` 之后不看 `ec`，失败被静默吞掉。
- **错标 `noexcept`**：一旦真抛出 → `std::terminate`（E.12、F.6）。
- **用 `assert` 当错误处理**：Release 构建里它消失，线上直接踩空指针。
- **对编程错误用异常**：把缺陷包装成"可处理的失败"，掩盖真正的错误来源（E.7、E.26）。
- **异常类型直接实现 `std::exception`**：绕开 `runtime_error` / `logic_error` 分类，除基类捕获外没人接得住（E.14）。
- **持有裸资源时抛异常**：展开时资源没人接管 → 泄漏；一律用 RAII（E.13、E.6）。

## Code Examples

```cpp
class DatabaseError : public std::runtime_error {
public:
    explicit DatabaseError(const std::string& what)
        : std::runtime_error(what) {}
};

class File {
    ~File() noexcept {          // ✓ 隐式 noexcept
        try {
            flush();
        } catch (...) {         // ✓ 只在边界兜底：吞掉并记录日志
            std::cerr << "flush failed in dtor\n";
        }
    }
};
```

- **What it demonstrates**: 异常要从 `std::runtime_error` 派生才能被 `catch (const std::exception&)` 接住（E.14）；析构绝不抛（E.16、C.37）。

```cpp
void might_throw() { /* ... */ }

static_assert(noexcept(might_throw()) == false);
static_assert(noexcept(std::vector<int>{}.size()) == true);   // 不会抛

void f() noexcept {
    throw std::runtime_error("x");   // ✗ 立即 std::terminate
}
```

- **What it demonstrates**: `noexcept` 把"会不会抛"变成可静态断言的契约；误标的后果只有进程当场终止（F.6、E.12）。

```cpp
#include <system_error>

std::error_code ec;
std::ifstream f("data.bin", std::ios::binary);
f.open("data.bin", ec);
if (ec) {
    log("open failed: " + ec.message() + " (" + ec.category().name() + ")");
}

if (ec == std::errc::permission_denied) { /* ... */ }
```

- **What it demonstrates**: `std::error_code` 把失败连同消息和错误类别一起带回来，且能与返回值共存。

```cpp
#include <expected>

std::expected<int, std::string> parse(const std::string& s) {
    try {
        return std::stoi(s);
    } catch (const std::exception& e) {
        return std::unexpected(std::string("bad number: ") + e.what());
    }
}

// 使用：必须显式处理错误
auto r = parse("42");
if (r) {
    use(*r);              // 有值
} else {
    log(r.error());       // 错误
}
```

- **What it demonstrates**: 失败被编码进返回类型，调用者不面对它就编译不过（C++23 已把 `std::unexpected` 更名为 `std::unexpect`）。

## Reference Tables

### 三种错误处理机制对比

| 机制 | 适用场景 | 优点 | 缺点 |
|---|---|---|---|
| **异常** `throw` | 异常情况确实罕见且无法就地处理 | 调用路径干净，不破坏控制流 | 有运行时开销，跨语言 ABI 麻烦 |
| **错误码 / `std::error_code`** | 预期内的失败（文件不存在、网络超时） | 无异常开销，可与返回值共存 | 调用者容易忘记检查 |
| **`std::expected`**（C++23） | 需要把"值或错误"一起传递 | 类型安全，强制处理 | 尚未普及 |

### 失败定性 → 机制选择

| 错误类型 | 例子 | 机制 |
|---|---|---|
| 编程错误（不该发生） | 数组越界、空指针解引用 | **不检查** —— 断言 / 崩溃 |
| 逻辑错误（调用者用错） | 无效参数、状态不对 | 抛 `std::logic_error`（或断言） |
| 运行时环境失败 | 文件不存在、网络超时 | `expected` / `error_code`（可预期） |
| 资源耗尽 | 内存不足 | 抛 `std::bad_alloc` |

### 异常安全三级保证

| 保证 | 含义 | 实现代价 |
|---|---|---|
| **基本保证** | 抛异常后程序仍有效，无资源泄漏、无不一致状态 | 低：成员交给 RAII |
| **强保证** | 抛异常后状态与调用前**完全相同**（事务性） | 中：先算后提交 |
| **不抛保证** | `noexcept`，不会抛异常 | 需先证明不会抛 |

## Worked Example

**场景**：文件导入服务同时服务内部 C++ 调用方和外部 C 调用方（跨语言 ABI，只吃整数错误码）。

**步骤 1｜先定性**：空指针参数是调用者用错方法 → 编程错误，在入口断言掉；文件缺失、权限不足是运行时失败 → 调用者有权决定重试还是报错（E.7、E.26）。

**步骤 2｜边界上选机制并固定**：内部一律抛异常（E.2、E.3），对外一律用 `std::error_code` + `std::errc`（跨编译器 ABI 用 C 风格子集，I.26）；纯 C++ 调用方要带自定义错误类型时换 `std::expected`。

**步骤 3｜错误类别可枚举**：`no_such_file_or_directory`、`permission_denied` 是调用方能据以分支的稳定类别。

**步骤 4｜内部异常成体系**：自定义异常继承 `std::runtime_error`（环境类失败）或 `std::logic_error`（调用方用错），别直接实现 `std::exception`（E.14）；持有句柄的类析构标 `noexcept`（E.16、C.37）。

**步骤 5｜需要原子性的更新用先算后提交**：

```cpp
void update(Container& c, const Item& item) {
    Item tmp = transform(item);      // 可能抛异常 → 此时 c 未被修改
    c.insert(tmp);                   // noexcept 的插入
}                                     // 强保证：要么全做，要么没做
```

**步骤 6｜边界翻译**，全库唯一的错误出口：

```cpp
// ✓ 边界层把内部异常翻译成对外的错误码
std::error_code read_file(const std::string& path, std::string& out) {
    try {
        out = load(path);
        return {};
    } catch (const std::exception& e) {
        log(e.what());
        return std::make_error_code(std::errc::io_error);
    }
}
```

**对照反例**：清理逻辑写成 `noexcept` 而内部会抛 → 当场 `std::terminate`，边界层的 `catch` 都来不及救：

```cpp
void flush_cache() noexcept {
    write_to_disk();                 // ✗ 内部可能抛 → std::terminate
}
```

**验证**：对不存在的路径断言 `read_file` 返回非空错误码；把 C ABI 目标文件用 `-fno-exceptions` 编一遍，藏着依赖抛异常的路径会当场暴露。

## Key Takeaways

1. 先定性再选机制：编程错误还是运行时失败，定性错了机制再花哨也是错的（E.4、E.7）。
2. 机制在边界选定并全库一致——内部异常，边界 `expected` / `error_code`（E.1、E.3、E.27）。
3. 析构、资源释放、`swap`、移动一律 `noexcept` 且永不失败（E.16、C.37、C.66、C.85）。
4. 强保证 = 先在临时对象上算，成功后再提交（E.6、E.19）。
5. `noexcept` 宁可漏标不要错标：错标的代价是 `std::terminate`（E.12、F.6）。
6. `catch` 先具体后一般，`catch (...)` 只出现在边界并记日志（E.17、E.31）。
7. `assert` 是开发者内部检查，不是错误处理：Release 下 `NDEBUG` 会让它消失。

## Connects To

- **Ch01**: RAII 与所有权——异常路径的资源释放靠 RAII（E.6、R.1）；析构 `noexcept` 是所有权纪律的最后一环（E.16、C.37）。
- **Ch02**: 移动语义——移动构造必须 `noexcept`（C.66），否则 `vector` 扩容退化成深拷贝（Per.14）。
- **Ch10**: 工具链与调试——`assert` 在 `NDEBUG` 下消失；`-fno-exceptions` 构建能逼出隐藏的异常依赖。
- **Ch05**: 并发下的异常传播——`future::get()` 会重抛任务里的异常，线程入口必须自己捕获（CP.60）；漏捕获即 `std::terminate`。
- **`std::expected`**：C++23 起把"值或错误"编码进类型，详见 Ch08。
- **`std::error_code` / `std::errc`**：跨编译器 ABI 用 C 风格子集（I.26）；错误类别可枚举，适合做策略分派。

### EXTRACT ch06
TERMS: 编程错误（programming error） | 运行时失败（runtime failure） | 异常安全三级保证（exception safety guarantees） | 异常规格（exception specification） | 按值抛出按引用捕获（throw by value, catch by reference） | 预期值（std::expected） | 错误码（error code / std::error_code） | 断言（assert）
PATTERNS: 边界翻译（何时用：库要对外暴露错误表达；做法：内部抛具体异常、边界 catch 后转成 error_code/expected，对外只暴露一种） | 先算后提交（何时用：需要强保证的更新操作；做法：可能失败的工作先在临时对象上做完，成功后再提交） | noexcept 契约标注（何时用：声明确定不抛或抛了也救不了的函数；做法：析构/释放/swap/移动一律标 noexcept，其余拿不准就不标）
DECISIONS: 当失败是调用者用错方法造成时选断言或直接崩而不选异常，因为用异常处理编程错误会掩盖缺陷来源（E.7、E.26） | 当接口要跨语言 ABI 时选 std::error_code 而非异常，因为异常穿不过 C 风格子集而错误码能携带稳定类别（I.26、E.28） | 当需要强保证时选先算后提交而非直接改目标对象，因为提交前的失败不会留下半完成状态（E.6、E.16）
TABLE: 三种错误处理机制（异常 / std::error_code / std::expected）对比适用场景、优点与缺点
