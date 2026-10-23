# Chapter 2: 移动语义与完美转发（Move Semantics & Perfect Forwarding）

## Core Idea

把「交出资源所有权」做成一次指针级操作（移动语义，move semantics）而不是深拷贝；
把实参的「值类别」原封不动传到下一层（完美转发，perfect forwarding）。

## Frameworks Introduced

- **值类别三分类（value categories）**
  - When to use: 判断表达式能否绑定 `T&&`、该选哪个重载。
  - How: 有名字可取地址 → 左值（lvalue）；临时量 → 纯右值（prvalue）；有名字但即将死亡 → 将亡值（xvalue）。只有后两类能绑 `T&&`。
- **`std::move` / `std::forward` 分工**
  - When to use: 手上具名对象要交出去；模板里要转发明来的值类别。
  - How: `std::move(x)` 无条件转 xvalue（放弃当前对象）；`std::forward<T>(x)` 有条件转发（原本是左值就仍按左值传）。
- **万能引用判定规则（universal reference）**
  - When to use: 写泛型包装器，要一套签名同时接左值和右值。
  - How: `T&&` 且 `T` 是纯类型推导（无修饰）才是万能引用，否则只是普通右值引用。
- **移动契约（move contract）**
  - When to use: 自己定义类型，或要把自定义类型放进 `std::vector`。
  - How: 移动构造/赋值标 `noexcept`（C.66），并把源置为「有效但未指定」（C.64）。
- **Rule of Five / Rule of Zero**
  - When to use: 决定要不要自己写拷贝/移动/析构。
  - How: 优先 Rule of Zero（C.20）；写了拷贝/移动/析构之一，五个就一起定义或一起 `=delete`（C.21）。
- **保证拷贝消除（guaranteed copy elision）**
  - When to use: 写工厂函数、返回大对象。
  - How: C++17 起用 prvalue 初始化、返回 prvalue 时拷贝/移动被**禁止**，直接构造。

## Key Concepts

- **移动语义（move semantics）**：移交资源所有权而非复制内容，O(n) → O(1)。
- **完美转发（perfect forwarding）**：模板把实参的值类别原样传下去。
- **左值 / 纯右值 / 将亡值**：C++11 起的表达式三分类，决定重载决议选拷贝还是移动。
- **`std::move`**：一个 `static_cast<T&&>`，只贴类别标签，不搬数据（ES.56）。
- **万能引用（转发引用）**：模板里纯推导出的 `T&&`，左右值都接。
- **接管型入参**：要拿走所有权 → `X&&` + `std::move`（F.18）。
- **转发型入参**：继续往下传 → `TP&&` + `std::forward`（F.19）。
- **移动后状态**：源对象必须「有效但未指定」（C.64）；`vector`/`string`/`unique_ptr` 额外保证为空。
- **`std::move_if_noexcept`**：`std::vector` 扩容时决定走移动还是回退拷贝。

## Mental Models

- **把移动想成「撕下所有权收据」**：原件撕走后源对象还得留一张「空但有效」的收据壳——所以置空源不是卫生问题，是正确性问题。
- **把 `std::move` 想成「贴标签」而非「搬家」**：它只改表达式类别，真正干活的永远是重载决议选中的那个函数。
- **把 `T&&` 想成一道带记录的窄门**：进门记下值类别，出门必须用 `std::forward` 原样带出；直接传参等于把记录扔了。

## Anti-patterns

- **`return std::move(local);`**：抑制 RVO/拷贝消除，源对象移动还可能抛异常。规则明文禁止（F.48）。
- **移动后继续读源**：`std::move(p)` 之后再 `use(*p)` 是 UB。
- **移动构造不置空源**：两个对象持有同一块内存 → 双重释放。
- **移动操作不标 `noexcept`**：`vector` 扩容悄悄退化成深拷贝（Per.14）。
- **转发时直接传参**：`target(arg)` 让右值降级成 const 左值，可移动变可拷贝。
- **`auto` 吞掉引用**：`auto b3 = b;` 把移动意图写成了拷贝（见 Ch11）。

## Code Examples

```cpp
class Buffer {
    int* data_;      // 堆指针
    std::size_t n_;
public:
    // 拷贝：申请新内存 + 复制内容 —— 昂贵
    Buffer(const Buffer& other) : data_(new int[other.n_]), n_(other.n_) {
        std::copy(other.data_, other.data_ + n_, data_);
    }
    // 移动：偷走指针，原对象置空 —— 几乎免费
    Buffer(Buffer&& other) noexcept
        : data_(std::exchange(other.data_, nullptr)), n_(std::exchange(other.n_, 0)) {}
};
```

- **What it demonstrates**: 同一类型里，拷贝是 O(n) 分配 + 复制，移动是 O(1) 指针交换 + 源置空。

```cpp
template <class T>
void relay(T&& arg) {                    // arg 这里是左值！
    target(std::forward<T>(arg));         // ✓ 转发出原始的值类别
}

template <class T>
void relay_bad(T&& arg) {
    target(arg);                          // ✗ 永远退化成拷贝
}
```

- **What it demonstrates**: 形参 `arg` 在函数体内已是左值，只有 `std::forward` 能还原调用方的值类别。

## Reference Tables

| 类别 | 含义 | 能否绑定到 `T&&` |
|---|---|---|
| **左值**（lvalue） | 有名字、可以取地址 | ✗ |
| **纯右值**（prvalue） | 临时量，如 `f()` 的返回值、`42` | ✓ |
| **将亡值**（xvalue） | 有名字但「即将死亡」，如 `std::move(x)` | ✓ |

| | 作用 | 用在哪 |
|---|---|---|
| `std::move(x)` | 无条件把 x 转成 xvalue | 明确放弃当前对象：存起来、交给接管型入参（F.18） |
| `std::forward<T>(x)` | **有条件**转发：x 是左值就当左值，是右值就当右值 | 模板里的完美转发（F.19） |

| 写法 | 万能引用？ | 能接什么 |
|---|---|---|
| `template <class T> void f(T&& x)` | 是 | 左值 + 右值 |
| `template <class T> void f(T& x)` | 否（左值引用） | 只接左值 |
| `void f(Widget&& x)` | 否（普通右值引用） | 只接右值 |
| `template <class T> void f(std::vector<T>&& x)` | 否（`T` 不纯） | 只接右值 |

## Worked Example

**目标**：写一个能放进 `std::vector` 的值类型 `Buffer`，配一条接管型入参、一条转发型入参，再写个工厂函数。

**步骤 1 — 定移动契约**：五个特殊成员函数一起写（C.21），移动标 `noexcept`（C.66），移动构造把源置空（C.64）。

```cpp
class Buffer {
public:
    Buffer() = default;
    explicit Buffer(std::size_t n) : data_(new int[n]), n_(n) {}

    Buffer(const Buffer& other) : Buffer(other.n_) {          // C.61 拷贝即复制
        std::copy(other.data_, other.data_ + n_, data_);
    }
    Buffer& operator=(const Buffer& other) {
        if (this != &other) { Buffer tmp(other); swap(tmp); } // C.62 自赋值安全
        return *this;                                         // F.47
    }
    Buffer(Buffer&& other) noexcept                            // C.66
        : data_(std::exchange(other.data_, nullptr)),
          n_(std::exchange(other.n_, 0)) {}                    // C.64 源置空
    Buffer& operator=(Buffer&& other) noexcept {               // C.63
        delete[] data_;
        data_ = std::exchange(other.data_, nullptr);
        n_ = std::exchange(other.n_, 0);
        return *this;
    }
    ~Buffer() { delete[] data_; }                             // C.31

    void swap(Buffer& other) noexcept {                       // C.83/C.85
        std::swap(data_, other.data_);
        std::swap(n_, other.n_);
    }
    std::size_t size() const noexcept { return n_; }
private:
    int* data_ = nullptr;
    std::size_t n_ = 0;
};
```

**步骤 2 — 选对入参形态**：接管用 `X&&`，转发用 `TP&&`，不可互换。

```cpp
Buffer g_buffer;

// 接管型：拿走所有权 → X&& + std::move（F.18）
void store(Buffer&& b) { g_buffer = std::move(b); }

// 转发型：原样传给下一层 → TP&& + std::forward（F.19）
template <class T>
void relay(T&& arg) { target(std::forward<T>(arg)); }
```

**步骤 3 — 工厂函数别自己制造移动**：C++17 起 `return b;` 直接在调用方对象上构造。

```cpp
Buffer make_buffer(std::size_t n) {
    Buffer b(n);
    return b;                 // ✓ 零次拷贝零次移动
}

Buffer make_buffer_bad(std::size_t n) {
    Buffer b(n);
    return std::move(b);      // ✗ 多余且有害：抑制了 RVO（F.48）
}
```

**步骤 4 — 验证收益**：

```cpp
std::vector<Buffer> v;
v.reserve(16);
v.push_back(make_buffer(1024));   // 工厂返回不产生拷贝/移动
Buffer b = std::move(v.front());  // ✓ O(1)：移动构造是 noexcept
auto c = v.front();               // ✗ 拷贝！auto 推导丢掉引用语义（见 Ch11）
```

**结果**：`push_back` 与工厂函数都零拷贝；`std::move(v.front())` 是 O(1) 指针交换，源对象变成空壳（`size()==0`，可析构、可重新赋值，不要读它的元素）。一旦从移动构造上去掉 `noexcept`，`vector` 扩容就会退化成整块深拷贝（Per.14）——这就是性能回归的真实来源。

## Key Takeaways

1. `std::move` 不移动任何东西，只把表达式变成 xvalue 让重载决议选中移动重载（ES.56）。
2. 移动构造/赋值必须 `noexcept`（C.66），否则 `vector` 扩容退化成深拷贝（Per.14）。
3. 移动构造必须把源置为「有效但未指定」（C.64），否则双重释放。
4. 接管型入参 `X&&` + `std::move`（F.18）；转发型入参 `TP&&` + `std::forward`（F.19）。
5. `T&&` 是不是万能引用，只看 `T` 是否纯推导。
6. C++17 起返回 prvalue 是语言保证的拷贝消除，`return w;` 就够（F.48）。
7. 移动是性能手段不是语义手段：先按值语义设计类型（Rule of Zero，C.20）。

## Connects To

- **Ch01**: 所有权基础——移动是所有权转移的具体手段。
- **Ch04**: 标准库里的移动性能——`vector`/`string`/`map` 的移动成本与移动后状态。
- **Ch08**: 现代 C++ 特性——C++17 保证拷贝消除、C++20 概念、C++26 P2266。
- **Ch11**: auto 与移动的坑——`auto` 推导吃掉引用，把移动意图变成拷贝。
- **F.19 / C.21 / C.66**: 完美转发、Rule of Five、移动 `noexcept` 的原文出处。

### EXTRACT ch02
TERMS: 移动语义（move semantics） | 完美转发（perfect forwarding） | 值类别（value categories） | 万能引用（universal reference） | 将亡值（xvalue） | 移动后状态（valid but unspecified） | 接管型入参（will-move-from parameter） | 转发型入参（forward parameter）
PATTERNS: 自定义值类型（何时用：要写移动构造+移动赋值并标 noexcept、源置空；不要默认 Rule of Five，优先 Rule of Zero） | 模板转发包装器（何时用：写 TP&& + std::forward<T>，不要用 const& 接一切） | 接管所有权接口（何时用：写 X&& + std::move，源对象此后按「有效但未指定」处理）
DECISIONS: 当 vector 扩容变慢时选移动构造标 noexcept，因为 std::move_if_noexcept 会因可能抛异常而回退到深拷贝 | 当写返回工厂函数时选 return w 而非 return std::move(w)，因为 C++17 起 prvalue 拷贝消除是语言保证且 std::move 会抑制 RVO（F.48） | 当转发实参时选 std::forward 而非直接传参，因为形参本身是左值，直接传会把右值降级成 const 左值导致拷贝
TABLE: 值类别（lvalue/prvalue/xvalue）× 能否绑定 T&&，与 std::move/std::forward 的无条件/有条件差异对照
