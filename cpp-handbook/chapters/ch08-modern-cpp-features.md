# Chapter 8: 现代 C++ 特性全景（Modern C++ Features）

## Core Idea

C++11 之后每个标准都在补同一类债——**让代码更安全、更易读、更并发友好**。要掌握的不是特性列表，而是"哪些特性改变了写法"：一条特性值不值得用，看它是否替掉了一整类旧写法。

## Frameworks Introduced

- **按标准版本的写法变化（Writing changes by standard version）**：每个标准一张表，逐条回答"这个特性替掉了什么"。
  - When to use: 定编译标准、评估升版本。
  - How: C++11 改"显式化"，C++17 改"解构"，C++20 改"约束"，C++23 改"错误"。
- **需求→标准选型决策表（Requirement-to-standard decision table）**：从"要表达什么"反推"该用哪个类型"。
  - When to use: 设计返回值、状态容器、错误通道。
  - How: 没有值 → `optional`；多类型择一 → `variant`；带错误 → `expected`（C++23）；模板约束 → Concepts；切片 → `string_view`。
- **接口签名现代化（Signature modernization）**：用值语义、视图类型、编译期约束重写签名。
  - When to use: 旧接口还带 `T* + len`、`bool` + 出参、裸 `new`。
  - How: 只读入参接 `const T&`、接管型入参接 `X&&`（F.16、F.18）；序列接 `std::span`（F.24、R.14）；字符序列接 `std::string_view`（SL.str.2）。
- **编译期化（Compile-time-ification）**：能在编译期算完的事不留到运行期。
  - When to use: 常量表、默认值、类型约束校验。
  - How: `constexpr`（Con.5、F.4、T.123）；`if constexpr` 做编译期分支；`static_assert` 校验概念（T.150）。

## Key Concepts

- **写法变化（writing change）**：特性替掉旧写法的程度决定优先级。
- **类型即文档（type as documentation）**：`optional`／`variant`／`expected` 把"没有值 / 多类型择一 / 带错误"编码进返回类型（E.1、E.3）。
- **视图类型（view type）**：`std::string_view`、`std::span` 只描述已有内存，不拥有它；活得比被看对象短即悬垂（R.4、R.14、F.24）。
- **概念约束（concept）**：C++20 把模板约束变成"写在签名里的要求"（T.10、T.11）。
- **保证拷贝消除（guaranteed copy elision）**：C++17 起返回 prvalue 不再要求可拷贝或可移动；写 `return w;` 而非 `return std::move(w);`（F.48）。
- **特殊成员函数纪律（special member functions）**：`= default` 或 `= delete`；动一个就要处理其余（C.21、C.66、C.67）。
- **类枚举（class enum / `enum class`）**：枚举不隐式转 `int`，作用域独立（Enum.3、Enum.7）。
- **标准契约（standard contract）**：项目只承诺一个标准版本，跨版本混用由构建配置挡住。

## Mental Models

- 把每个标准版本当一次**写作风格迁移**：C++11 迁移"显式化"，C++17 迁移"解构"，C++20 迁移"约束"，C++23 迁移"错误"；每层只问：这一版替掉了哪种旧写法。
- 把 `auto` 当**"类型由谁决定"的开关**：`auto` 决定值类型（会拷贝），`auto&` 决定引用，要移动只能显式写 `auto&&` + `std::move`（ES.11、ES.56、F.18）。
- 把视图类型当**借来的窗户**：窗户没责任，被看的房间一拆窗户就成野指针——有效期由调用方保证（R.4、R.14）。
- 把 `optional`／`variant`／`expected` 当**"把状态写进类型"**：状态越具体，分支越少（E.1、E.3）。

## Anti-patterns

- **编译标准没定就写特性**：C++17 项目里用 Concepts、C++20 项目里用 `std::expected`——用构建配置挡住。
- **`auto` 吃掉引用**：`auto x = f();`（`f` 返回引用）与 `auto x = std::move(v);` 都拷贝，只有 `auto&&` 保持引用（ES.11、ES.56；见 Ch02）。
- **视图活得比被看对象短**：`std::string_view sv = std::string("tmp");`，或 `std::span` 指向会扩容的 `vector`（R.4、R.14）。
- **手写 `union` + 魔法 tag 代替 `variant`**：漏设 tag 就是未定义行为（C.181）。
- **用「返回 bool + 出参」表达"可能没有值"**：漏看返回值即静默错误；改用 `std::optional`（F.21）。
- **Concepts 与 SFINAE 混用**：同一代码库两套约束写法；选定一套（T.10、T.11；T.48 只在编译器不支持时回退）。
- **`std::move` 到处撒**：打断拷贝消除、误伤后续使用（ES.56、F.48）。
- **先上观望层特性**：反射、`std::simd`、契约的工具链尚未就绪。

## Code Examples

```cpp
// 结构化绑定
auto [name, age] = person;                 // 聚合体
for (const auto& [k, v] : map) { ... }      // 遍历 map

// if constexpr
if constexpr (std::is_integral_v<T>) {
    return x + 1;      // 非整型时这段代码根本不参与编译
} else {
    return x.to_double();
}
```

- **What it demonstrates**: 结构化绑定负责解构，`if constexpr` 让分支不进运行期——两者都不产生运行时代价。

```cpp
// 三路比较
struct Version {
    int major, minor, patch;
    auto operator<=>(const Version&) const = default;   // 自动生成全部比较
};

// span
void process(std::span<const std::byte> data);
```

- **What it demonstrates**: `= default` 生成全部比较运算符；`std::span` 用一个视图替掉"指针 + 长度"（F.24）。

## Reference Tables

### 按标准版本的特性与它改变了什么

**C++11：现代 C++ 的起点**

| 特性 | 改变了什么 |
|---|---|
| `auto` | 类型推导，不再手写一长串模板参数 |
| `nullptr` | 取代 `NULL`/`0`，类型安全 |
| 范围 `for` | 遍历容器不用写 iterator 样板 |
| Lambda | 匿名函数，能捕获局部变量 |
| `unique_ptr` / `shared_ptr` | 所有权显式化（R.20、R.21、R.23） |
| `std::move` / `std::forward` | 移动语义 |
| `constexpr` | 编译期求值（单表达式） |
| 初始化列表 `{}` | 统一初始化，防窄化转换 |
| `= delete` / `= default` | 显式控制特殊成员函数（C.21） |
| `std::thread` / `std::mutex` | 标准多线程 |
| `emplace_back` / `emplace_front` | 原地构造，避免临时对象 |
| 变参模板 | 泛型转发、参数包 |
| `noexcept` | 异常规格现代化 |
| 强类型枚举 `enum class` | 避免隐式转 int（Enum.3） |

**C++14**

- 泛型 lambda：`[](auto x){ ... }`；lambda 初始化捕获：`[x = std::move(v)]{}`（C++14 正式化）
- `std::make_unique`（R.23）
- 弃用 `std::random_shuffle` → `std::shuffle`

**C++17**

| 特性 | 影响 |
|---|---|
| **结构化绑定** | 解构 tuple / pair / 聚合体 |
| **if / switch 初始化语句** | 缩小变量作用域 |
| **保证拷贝消除** | 返回临时对象零拷贝（重大）（F.48） |
| `constexpr if` | 编译期分支，替代大量模板特化 |
| **嵌套命名空间** | `namespace a::b::c {}` |
| `inline` 变量 | 头文件里定义变量 |
| **折叠表达式** | 变参模板简化 |
| `std::optional` | 表达"可能没有值" |
| `std::variant` | 类型安全的联合体 |
| `std::any` | 任意类型容器 |
| `std::string_view` | 非拥有字符串视图（SL.str.2） |
| `std::filesystem` | 标准文件系统 |
| `[[nodiscard]]` | 标记必须检查的返回值 |
| `[[maybe_unused]]` | 抑制未使用警告 |
| `[[fallthrough]]` | 标注故意贯穿 |
| `if constexpr` | 编译期条件 |
| CTAD | 类模板参数推导（`std::pair p{1, 2.0};`） |

**C++20：迄今最大的一个版本**

| 特性 | 影响 |
|---|---|
| **Concepts** | 模板约束可读化（见 Ch03）（T.10、T.11） |
| **Ranges** | 更安全、更可组合的算法（见 Ch04） |
| **协程** | 异步用 C++ 写，不用回调地狱（CP.51） |
| **Modules** | 编译速度的大杀器（生态仍在完善） |
| `constexpr` 增强 | 允许循环、虚函数（部分）（Con.5） |
| `consteval` / `constinit` | 强制编译期求值 / 保证静态初始化 |
| **三路比较** `<=>` | 自定义比较运算符一键生成 |
| `std::span` | 连续内存视图（F.24、R.14） |
| `std::jthread` | 自动 join 的线程（CP.23） |
| `std::atomic_ref` | 对已有对象做原子操作 |
| designated initializers | `Point{.x = 1, .y = 2}` |
| `std::source_location` | 获取调用点信息（日志/断言） |
| `std::bit_cast` | 位级重解释 |
| `std::endian` | 字节序判断 |
| `[[likely]]` / `[[unlikely]]` | 分支预测提示 |
| `u8"..."` | UTF-8 字符串字面量 |
| `std::format`（C++20 部分实现） | 类型安全格式化 |

**C++23**

- `std::expected` —— 错误处理（见 Ch06）；`std::mdspan` —— 多维数组视图
- `std::print` / `std::println` —— **标准输出**（终于不用 `iostream` 了）
- `if consteval`；推导指引（deduction guides）增强；`std::to_underlying`；`std::byteswap`
- `std::stacktrace` —— **获取调用栈**（调试利器）；`std::unreachable`
- 移除 `std::random_shuffle`、`std::terminate` 的一些限制；`import std;` —— 标准库模块

**C++26（进行中）**

> 下表是**已采纳提案的归纳**，不是某个单一来源的逐条摘录。教程的 C++26 章节定位为"展望"。

- **P2266 Simpler implicit move** —— 隐式移动规则大幅简化
- `std::text_encoding` —— 字符编码标准库支持
- 契约（Contracts）—— `precondition`/`postcondition` 进语言
- `std::simd` —— SIMD 库
- 反射（Reflection）—— **终于要有原生反射了**
- `std::optional` 的 `and_then` 等增强；更强的 `constexpr`

### 真正改变写法的特性（优先级阶梯：★★★★★ 必须掌握 → ★★★☆ 强烈建议 → ★★☆☆ 了解即可 → ★☆☆☆ 观望）

| 级别 | 含义 | 特性 |
|---|---|---|
| ★★★★★ | 必须掌握 | `auto` / `nullptr` / 范围 for / lambda / 智能指针 / 移动语义 / 结构化绑定 / `if constexpr` / `constexpr` / `[[nodiscard]]` / `std::optional` / `std::variant` / `std::string_view` / Concepts / Ranges |
| ★★★☆ | 强烈建议 | `std::filesystem` / `std::jthread` / 三路比较 / `std::span` / 折叠表达式 / designated initializers |
| ★★☆☆ | 了解即可 | Modules / 协程 / `std::expected` / `std::print` / `consteval` / `std::source_location` / `std::stacktrace` |
| ★☆☆☆ | 观望 | 反射 / `std::simd` / 契约（生态与工具链尚未就绪） |

### 选型决策表

| 需求 | C++17+ | C++20+ | C++23+ |
|---|---|---|---|
| "可能没有值" | `std::optional<T>` | 同 | 同 |
| "多个类型择一" | `std::variant<A,B>` | 同 | 同 |
| "可能失败并带错误" | `std::pair<T,E>` | 同 | `std::expected<T,E>` |
| 遍历序列 | 迭代器 | `std::ranges` | 同 |
| 模板约束 | SFINAE | **Concepts** | 同 |
| 字符串切片 | `std::string_view` | 同 | 同 |
| 格式化输出 | `std::to_string`/fmtlib | `std::format`（部分） | `std::print` |

## Worked Example

**场景**：一个 C++11 时期的配置解析模块，接口全是旧写法；不改业务逻辑迁到 C++20。

**改造前**：

```cpp
// ✗ 魔法 tag + 裸 union；bool + 出参；指针 + 长度
enum class ValueKind { Int, Real, Text };

struct Value {
    ValueKind kind;                        // 魔法 tag
    union { int i; double d; std::string s; } data;
};

bool parse_int(const std::string& text, int& out);       // bool + 出参
const char* name_of(const Value* v, std::size_t n);      // 指针 + 长度
```

**步骤 1｜先定标准契约**：定 C++20 ⇒ 可用 Concepts／Ranges／`std::span`；`std::expected` 要等 C++23，"带错误的失败"暂用 `std::optional`（决策表第 3 行）。

**步骤 2｜换返回类型与状态容器**：`bool` + 出参 → `std::optional<int>`（F.21）；`union` + `kind` → `std::variant<int, double, std::string>`，tag 漏设这类未定义行为消失，访问改用 `std::visit`（C.181 的反面）。

**步骤 3｜换参数类型**：`const std::string&` → `std::string_view`（SL.str.2）；`(const Value*, std::size_t)` → `std::span<const Value>`（F.24、R.14）。

**步骤 4｜模板约束上移**：`enable_if` → 概念，约束写进签名（T.10、T.11）；`static_assert` 校验（T.150）。

**改造后**：

```cpp
struct Value {
    std::variant<int, double, std::string> data;
    auto operator<=>(const Value&) const = default;      // 六个比较运算符一次生成
};

template <typename T>
concept IntegerLike = std::integral<T>;

template <IntegerLike T>
std::optional<T> parse_int(std::string_view text) {
    T out{};
    if (!consume_digits(text, out))
        return std::nullopt;                             // ✗ 过去是"返回 false"
    return out;                                         // C++17 起保证拷贝消除
}

static_assert(IntegerLike<int>);                       // 编译期检查（T.150）

std::string_view name_of(std::span<const Value> values);  // 取代指针 + 长度
```

**验证**：Concepts 把"传错类型"从运行期挪到编译期（T.10）；`std::optional` 的"没有值"必须显式处理，`[[nodiscard]]` 把漏处理变成警告；视图的有效期从"签名保证"变成"调用方保证"——这是本次改造唯一要写进文档的约定。升到 C++23 时把"带错误"的返回换成 `std::expected<T,E>`，其余不动（见 Ch06）。

## Key Takeaways

1. 学特性只看"改变了写法"的那部分；标准越新不等于越该用，按优先级阶梯取用。
2. 需求→类型：`optional`（可能没有值）／`variant`（多类型择一）／`expected`（带错误，C++23）不可互换（E.1、E.3）。
3. 视图类型替掉"指针 + 长度"和只读字符串拷贝，但有效期由调用方负责（R.14、F.24、SL.str.2）。
4. C++20 项目里模板约束统一用 Concepts，不要和 SFINAE 混用（T.10、T.11、T.48）。
5. `= default`／`= delete` 是特殊成员函数的唯一正解：动一个就要处理其余（C.21、C.66、C.67）。
6. 编译标准是契约：写进构建配置，并在 CI 上按目标标准实编一次。
7. 观望层特性（反射、SIMD、契约、Modules、协程）生态未就绪，先别上。

## Connects To

- **Ch02**: `auto` 吃掉引用、`= default` 特殊成员函数、保证拷贝消除（F.48、C.21、C.66）。
- **Ch03**: Concepts 的完整用法与 SFINAE 对比（T.10、T.11、T.48）。
- **Ch04**: Ranges 取代迭代器拼装、`std::span` 接连续序列（R.14、F.24）。
- **Ch06**: `std::expected` 把"值或错误"编码进类型（E.1、E.3）。
- **Ch05**: `std::jthread`（C++20）是"线程即作用域容器"的标准库版本（CP.23、CP.26）。
- **Ch09**: 标准版本与构建配置的选择最终落地在构建脚本里。

### EXTRACT ch08
TERMS: 写法变化（writing change） | 视图类型（view type） | 类型即文档（type as documentation） | 概念约束（concept） | 保证拷贝消除（guaranteed copy elision） | 特性优先级阶梯（feature priority ladder） | 标准契约（standard contract）
PATTERNS: 需求驱动的返回类型（何时用：表达"可能没有值/多类型择一/带错误"；做法：optional/variant/expected 三选一，别用 bool+出参或 union+tag） | 接口签名现代化（何时用：旧接口还用裸指针+长度或 const std::string& 接只读入参；做法：换 span/string_view，视图有效期由调用方保证） | 编译期化（何时用：常量、类型约束校验、同构分支；做法：constexpr/if constexpr/static_assert，把运行期检查挪到编译期）
DECISIONS: 当要表达"可能没有值"时选 std::optional 而非 bool+出参，因为出参方案漏看返回值就是静默错误（F.21） | 当 C++20 项目写模板约束时选 Concepts 而非 SFINAE，因为约束写进签名后错误信息与重载解析都可读（T.10、T.11） | 当要表达"多类型择一"时选 std::variant 而非 union+魔法 tag，因为裸 union 漏设 tag 就是未定义行为（C.181）
TABLE: 按标准版本的特性（标准版本 × 特性与它改变了什么写法）与需求选型（需求 × C++17+/C++20+/C++23+）
