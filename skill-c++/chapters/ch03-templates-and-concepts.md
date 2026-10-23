# Chapter 3: 模板与 Concepts（Templates & Concepts）

## Core Idea

把约束写进签名：模板是编译期的代码生成器，Concept（C++20 概念）把「哪些类型能用这个函数」从 SFINAE 的重载筛除搬进签名本身，让约束一眼可见，而不是藏在实现细节里。

## Frameworks Introduced

- **两阶段名字查找（two-phase name lookup）**：模板名字查找分两轮——定义时（普通查找 + 依赖名 ADL）、实例化时（依赖名在实例化点才解析）。
  - When to use: 排查「基类有成员却找不到」「后面才声明的函数却报未定义」。
  - How: 非依赖名定义时不可见就永远不可见；依赖名必须 `typename` 标类型、`this->` 标成员（T.60）。
- **SFINAE（Substitution Failure Is Not An Error）**：替换失败时把候选从重载决议中剔除，而不是报错。
  - When to use: 不能用 C++20、或要兼容旧编译器。
  - How: `std::enable_if` 过滤类型、`std::void_t` 做检测惯用法；代价是错误信息难读，约束与签名分离。
- **Concepts（C++20）——把约束写进签名**：约束直接写在模板参数表里，取代 SFINAE。
  - When to use: 所有新写的泛型接口（C++20 起默认用 concept），前提是模板用对位置：T.1 / T.2 / T.3。
  - How: 先查标准概念（`std::integral`、`std::same_as`，T.11），不够再自写 `requires` 表达式；单类型参数用简写（T.13）。
- **约束偏序（subsumption）**：更特化的 concept 优先于更一般的。
  - When to use: 给某一类类型换一套实现，同时保留通用版本。
  - How: 定义 `Number`（泛）与 `Integer`（特）两个 concept，同名函数模板各写一份，编译器自动选更特化的，无需全特化。
- **万能引用（forwarding reference）与完美转发**：只有 `template <class T> void f(T&&)` 且 `T` 纯推导时才是万能引用。
  - When to use: 写工厂、包装器这类需要原样传递实参的模板。
  - How: 内部一律 `std::forward<T>(x)`（F.19）；加了 `const`、`&` 或 `T` 非纯推导 → 退化成普通右值引用。
- **CRTP（奇异递归模板模式）**：把派生类类型作为基类模板参数传进去，实现零开销静态多态。
  - When to use: 性能关键路径需要多态，但不想付虚函数与虚表成本。
  - How: 基类里 `static_cast<Derived*>(this)->execute()`；代价是不能用基类指针统一处理派生类（T.80）。

## Key Concepts

- **模板实例化（instantiation）**：用具体实参替换模板参数生成实际代码；每个实例化是一份独立代码。
- **非类型模板参数（non-type template parameter）**：编译期常量实参（如 `int N`），可用于数组长度；`template <auto Value>` 自动推导类型（C++17）。
- **依赖名（dependent name）**：含义取决于模板参数的名字；依赖基类成员必须 `this->`，依赖类型必须 `typename`。
- **Concept（概念）**：对一组类型的编译期谓词，由原子约束与 `requires` 表达式合取而成。
- **requires 表达式 vs requires 子句**：前者是 `{ os << v; }` 这样的需求列表，后者是 `requires std::same_as<T, int>` 这样的附加约束。
- **约束偏序（subsumption）**：概念 A 蕴含 B 时 A 更特化，重载决议优先选 A。
- **万能引用与完美转发**：纯推导 `T` 下的 `T&&`；左值折叠成 `T&`，右值折叠成 `T&&`；完美转发保持实参的值类别。
- **模板元编程（template metaprogramming）**：在编译期算类型与值；只在真需要时才用（T.120），优先用标准库设施（T.124）。

## Mental Models

- **把模板当编译期的宏展开**：不是「一次写多次用」的运行时多态，而是「一份源码、按实参展开成多份代码」——展开前的错误信息必然难懂。
- **把 Concept 当签名的一部分，不是附加的检查**：SFINAE 是重载决议的旁路筛子，Concept 是候选签名的一部分，这决定二者的错误信息与偏序行为完全不同。
- **把万能引用理解成「`T` 还没被推导出来」**：只有 `T` 纯推导时 `T&&` 才有「万能」语义；写了 `const`、`&` 或显式模板实参，它就只是普通右值引用。
- **把 CRTP 理解成「基类持有派生类指针」**：静态多态 = 编译期定下 `Derived` + 运行时零成本跳转，代价是不能用基类指针统一处理派生类。

## Anti-patterns

- **无约束的高可见度模板**：`void print(T)` 会抢走本该匹配的其它重载（T.47），表现为「莫名其妙调到了模板版本」。
- **C++20 项目里继续用 SFINAE 表达约束**：约束与签名分离在两处，错误信息退化成天书；旧代码才按 T.48 用 `enable_if` 伪造。
- **特化函数模板**：破坏 ODR、难与重载组合；改用重载或标签分派（T.144 / T.65 / T.67）。
- **依赖基类成员不写 `this->`**：两阶段查找下，定义时编译器不知道 `T` 有没有该成员，直接报错。
- **在模板里做重运算**：每个实例化都编译一遍，重度模板库头文件可能编译几十秒；用 `-ftime-report` 定位。
- **模板里写非限定的非成员函数调用**：会无意间成为 ADL 定制点，绑定到你不想要的类型（T.69）。

## Code Examples

```cpp
#include <concepts>

template <typename T>
concept Streamable = requires(std::ostream& os, const T& v) {
    os << v;                       // 必须能流式输出
};

template <Streamable T>
void log(const T& v) { std::cout << v << '\n'; }
```

- **What it demonstrates**: 约束写在参数列表里，不匹配时错误直接指向 concept 定义。

```cpp
// 错误 1：依赖基类（dependent base class）的成员必须用 this-> 或 typename
template <class T>
void f(const T& t) {
    t.size();      // ✗ 编译器不知道 T 有没有 size()
}

// 错误 2：非依赖名必须在定义时可见
template <class T>
void g() {
    helper();     // ✗ helper 在定义点找不到就不会在实例化点再找
}
```

- **What it demonstrates**: 两阶段名字查找的两类经典报错与各自修法。

```cpp
template <class T> void f(T&& x);                 // 万能引用
template <class T> void f(const T&& x);           // 普通右值引用
template <class T> void f(std::vector<T>&& x);    // 普通右值引用
```

- **What it demonstrates**: 万能引用的判定——只有纯推导的 `T` 才享受折叠语义。

## Reference Tables

| 模板最佳实践 | 原因 |
|---|---|
| 头文件里定义模板，而非 `.cpp` | 编译器需要看到定义才能实例化 |
| 用 `template <class T>` 而非 `typename` 统一风格 | 一致性；`typename` 只在依赖上下文中必需 |
| 约束写在参数列表（Concepts） | 错误信息可读 |
| 模板参数包放最后 | 便于推导 |
| 避免在模板里做重运算 | 每个实例化都会编译一遍 |

## Worked Example

**上下文**：日志模块要提供 `log_value(x)`，只接受能写到 `std::ostream` 的类型；调用方会传错类型，需要可读的报错。

**第 1 步（❌ SFINAE 版）**：

```cpp
template <class T>
typename std::enable_if<std::is_streamable<std::ostream&, T>::value>::type
log_value(T&& x) { std::cout << x; }
```

`log_value(42)` 通过，`log_value(Widget{})` 编译失败——报错把 `enable_if` 的整条实例化路径摊开成模板回溯，调用方要自己读出「Widget 不能流式输出」。

**第 2 步（✅ 换成 Concept）**：

```cpp
template <typename T>
concept Streamable = requires(std::ostream& os, const T& v) {
    os << v;
};

template <Streamable T>
void log_value(T&& x) { std::cout << x << '\n'; }
```

现在 `log_value(42)` 推导出 `T = int&`；类型不支持 `<<` 时，报错直接指向 `Streamable` 那一行，并说明 `std::ostream& << const T&` 是否成立。约束从此是「类的属性」，可顺手加一道编译期体检：

```cpp
static_assert(Streamable<int>);
static_assert(!Streamable<Widget>);   // T.150：用 static_assert 检查类是否匹配 concept
```

**第 3 步（要特化就用偏序，别特化函数模板）**：

```cpp
template <typename T> concept Number  = std::integral<T> || std::floating_point<T>;
template <typename T> concept Integer = std::integral<T>;

template <Number T>  void log_value(T&& x) { std::cout << "num: " << x << '\n'; }
template <Integer T> void log_value(T&& x) { std::cout << "int: " << x << '\n'; }
```

`Integer` 蕴含 `Number`（`std::integral` 蕴含 `integral || floating_point`），编译器自动选更特化的 `Integer` 版本；写的是重载而非 `template <>` 全特化，没有 ODR 问题（T.144）。

**结果**：约束集中在 `Streamable` 一个 concept 里，签名只写 `template <Streamable T>`；报错点名 concept；整数类型自动走专门实现。若要兼容 C++17，把 concept 降级成 `enable_if`（T.48），但保留 concept 定义作单一真相源。

## Key Takeaways

1. 新写的泛型接口先问：C++20 可用就写 concept，约束写在参数列表里，别藏在 `enable_if` 里（T.10 / T.11）。
2. 优先用标准 concept；自写 concept 按「使用模式」定义、要求完整操作集合（T.21 / T.26），只提必要属性（T.41）。
3. 同一类型约束用简写 `std::same_as<T, int>` 而非自造 concept（T.13）；少用 `!C<T>` 与 `C1<T> || C2<T>`（T.30 / T.31）。
4. `T&&` 只有在 `T` 纯推导时才是万能引用；转发一律 `std::forward`，参数分类照 F.16–F.19，多返回值返回结构体（F.21）。
5. 要「换个实现」就用重载 + 约束偏序或标签分派，别特化函数模板（T.144 / T.65）。
6. 模板的真实成本是编译时间：能移到编译期的搬过去（Per.11），别在模板里做重运算。

## Connects To

- **Ch08**: 现代 C++ 特性 —— Concepts 是 C++20 的标志性特性，requires 子句与约束偏序的标准写法在那里展开。
- **Ch02**: 移动语义与完美转发 —— 万能引用的折叠规则与 `std::forward` 的时机建立在移动语义上。
- **Ch04**: STL 容器与算法 —— 容器与算法的通用性来自模板（T.3）；分配器决定 `vector` 的内存行为。
- **Ch11**: 陷阱与反模式 —— 宏 vs 模板的边界，以及模板层的反模式清单。
