# Chapter 11: 陷阱与反模式（Pitfalls & Antipatterns）

## Core Idea

C++ 的坑只有三类根因——**未定义行为（UB, undefined behavior）**、**所有权错乱**、**API 误用**；能被工具检出的坑都不该靠人肉记，写完先问"哪个工具能报出它"。

## Frameworks Introduced

- **三问式（坑 → 后果 → 工具）**：①会出什么事 ②静默错还是崩溃 ③哪个工具能查出来。
  - When to use: Code Review、新人规范、上线前自检。
  - How: 查下方工具对照表；没有工具的条目只能靠人读代码。
- **三分类框架**：UB（编译器可假设它不发生）／所有权错乱（谁销毁、活多久）／API 误用（名字承诺 ≠ 实际行为）。
  - When to use: 拿到"跑得好好的"可疑代码，不知从哪下手。
  - How: 先归类再选工具：UB 交 UBSan／ASan；所有权交 ASan＋LSan；API 误用读签名。
- **双防线**：编译期钉死能静态判定的，运行期兜住剩下的。
  - When to use: 新项目初始构建、往 CI 加门禁。
  - How: 编译期 `-Wall -Wextra -Wpedantic -Werror`；运行期 `-fsanitize=address,undefined`。

## Key Concepts

- **未定义行为（undefined behavior）**：标准不规定结果，编译器可假设它不发生；"今天能跑"不是保证。
- **悬垂引用（dangling reference）**：指向已销毁对象或已释放内存的引用／指针／视图。
- **迭代器失效（iterator invalidation）**：容器结构变化后旧迭代器不再指向原元素。
- **静态初始化顺序（static initialization order）**：跨翻译单元的全局对象构造顺序未定义。
- **auto 退化（auto decay）**：`auto` 按值推导时丢掉引用与 `const`。
- **静默失败（silent failure）**：不崩溃、不报警告，只是结果错了——最贵的一类 bug。

## Mental Models

- 把 UB 想成"和编译器签了契约、你违约了"：编译器据此自由优化，换编译器或优化级别就崩。
- 把 `auto` 想成"值类别的复印机"：照抄类型时把引用和 `const` 一起复印没了。
- 把 API 名字想成"承诺"：`remove` 承诺重排，`erase` 承诺改大小。

## Anti-patterns

- **返回局部引用／lambda 引用捕获逃逸、迭代中 `push_back` 仍用旧迭代器** → 悬垂读或迭代器失效，UB；工具：ASan、Clang `-Wdangling`、`-D_GLIBCXX_DEBUG`（F.43、F.53）。
- **`std::remove` 忘了配 `erase`** → `size()` 不变，静默错；工具：编译器不报，靠 Review 查"remove 后紧跟 erase"，C++20 用 `std::erase_if`。
- **`int` 与 `size_t` 混比、有符号整数溢出** → 负数转巨大无符号数（恒真、越界）、溢出即 UB；工具：`-Wsign-compare`、UBSan `signed-integer-overflow`（ES.100、ES.103、ES.107）。
- **宏当函数（参数求值两次）、头文件里定义 `min`／`max`** → 副作用重复、污染全部包含者；工具：clang-tidy `cppcoreguidelines-macro-usage`（ES.31、ES.33）。
- **多态基类没有虚析构** → 经基类指针 `delete` 只跑基类析构，泄漏＋UB；工具：`-Wdelete-non-virtual-dtor`（C.35、C.127）。
- **特殊成员函数只写了一半** → 拷贝赋值仍可用，浅拷贝＋双重释放；工具：编译器报错、`-Wdeprecated-copy`（C.21、C.81）。
- **跨翻译单元的非平凡全局对象** → 用到尚未构造的对象，UB；工具：Clang `-Wglobal-constructors`；解法是藏进函数里的局部静态（I.22、R.6）。
- **`auto` 丢引用丢 `const`** → 多余拷贝，`'a'` 推成 `char`；工具：clang-tidy `performance-unnecessary-copy-initialization`（ES.11、ES.25）。
- **浮点用 `==` 比较** → 几乎恒不等，分支走错；工具：clang 分析器 `core.FloatEquality`，改 `std::abs(a-b) < eps`。
- **`goto` 跨初始化、`i = i++`、越界读这类"合法但诡异"的代码** → 前者编译错误、后者 UB；工具：编译器、UBSan（含 `bounds`）、ASan（ES.43、ES.76）。

## Code Examples

```cpp
// ✗ 三个坑叠在一起
std::vector<int> drop_bad(std::vector<int> v, int bad) {
    for (int i = 0; i < v.size(); ++i)                  // ③ int 与 size_t 混比
        if (v[i] == bad) v.push_back(0);                 // ① 扩容 → 迭代器失效
    std::remove(v.begin(), v.end(), bad);                // ② 只重排，size() 不变
    return v;
}

// ✓ 三处都改掉：下标用 size_t、不在迭代中改容器、remove 后补 erase
std::vector<int> drop_bad(std::vector<int> v, int bad) {
    for (std::size_t i = 0; i < v.size(); ++i)
        if (v[i] == bad) v.erase(v.begin() + i);
    v.erase(std::remove(v.begin(), v.end(), bad), v.end());
    return v;
}
```

- **What it demonstrates**: 三个坑各自的触发点与修法。

## Reference Tables

### 工具对照（工具 → 查什么 → 何时跑）

| 工具／开关 | 查什么 | 何时跑 |
|---|---|---|
| `-Wsign-compare` | 符号比较（ES.100） | 编译期 |
| `-Wdelete-non-virtual-dtor` | 缺虚析构（C.35） | 编译期 |
| ASan `-fsanitize=address` | 悬垂、越界、泄漏 | CI |
| UBSan `-fsanitize=undefined` | 有符号溢出、越界索引 | CI |
| TSan `-fsanitize=thread` | 数据竞争（CP.2） | 夜间 |
| clang-tidy `cppcoreguidelines-macro-usage` | 函数宏、宏污染（ES.31） | 提交前 |

### 写法选型（场景 → 写法 → 规则号）

| 场景 | 写法 | 规则号 |
|---|---|---|
| 入参 | 只读 `const T&`；要改 `T&` | Con.3、F.16、F.17 |
| 接管所有权 | `T&&`＋`std::move` | F.18、R.32 |
| 类型别名 | `using X = ...`（`typedef` 无别名模板） | T.42、T.43 |
| `auto` 留引用／`const` | `auto&`／`const auto&` | ES.11、ES.25 |
| 头文件 | 只声明不定义＋include guard | SF.2、SF.8、SF.11 |
| 默认实参 | 昂贵或有副作用的默认值改重载 | C.140 |

## Worked Example

**场景**："本地测试全过、上线偶发崩溃"的日志过滤器，四个坑叠在一起。

**步骤 1｜先归类再定位**：崩溃属"所有权错乱"。用 ASan 跑测试，报告 `heap-use-after-free`，指向 `label_of()` 返回的引用。

**步骤 2｜按类修**：悬垂 → 返回 `std::string` 而非引用（F.43）；迭代器失效 → 只读源容器、结果写新容器；`remove` 不删 → 补 `erase`；符号混用 → 下标统一 `std::size_t`（ES.100）。

**步骤 3｜复验**：同一测试集在 `-O0` 与 `-O2` 各跑一遍（UB 随优化级别变结果），并要求 `-Werror` 下零告警。

**结果**：四个根因各有一条确定报告，"偶发崩溃"变成"CI 必现失败"。

## Key Takeaways

1. 每个坑先问"哪个工具能查出来"；查不到工具的代码＝需要补测试。
2. 编译期能挡的别留到运行期：`-Werror` ＋ ASan/UBSan 一起进 CI（P.12）。
3. `remove` 只重排、`erase` 才改大小；`auto` 会复印掉引用和 `const`。
4. 长度与下标统一 `std::size_t`，别让 `-1` 变成巨大无符号数（ES.100、ES.107）。
5. 多态基类一律虚析构、不可拷贝类型写全特殊成员函数（C.35、C.21）；UB 是定时炸弹，`i = i++` 必须删（ES.43）。

## Connects To

- **Ch01**: 悬垂与所有权的系统性解法（R.3、R.4、F.43）。
- **Ch02**: `auto` 吃掉引用、`= default` 特殊成员函数（F.45、F.48、C.66）。
- **Ch04**: 迭代器失效与 `std::remove` 的完整规则（ES.71、R.14）。
- **Ch05**: 数据竞争类陷阱与 TSan（CP.2、CP.9）。
- **Ch06**: 编程错误与运行时错误的分界（E.1、E.6）。
- **Ch10**: 把 Sanitizer 与编译告警工程化接入流水线。

### EXTRACT ch11
TERMS: 未定义行为（undefined behavior） | 悬垂引用（dangling reference） | 迭代器失效（iterator invalidation） | 静默失败（silent failure） | 静态初始化顺序（static initialization order） | auto 退化（auto decay）
PATTERNS: 三问式审坑（何时用：写完可疑代码；做法：坑→后果→工具，查不到就补测试） | 双防线配置（何时用：新项目或加 CI；做法：编译期 -Werror 全开，运行期 ASan+UBSan） | 默认不可变签名（何时用：写函数参数；做法：只读 const&、要改 &、接管 &&）
DECISIONS: 删容器元素选 erase(std::remove(...), end()) 而非裸 remove，因为 remove 只重排不改 size() | 多态基类选 public virtual ~Base() 而非非虚析构，因为经基类指针 delete 会漏掉派生析构（C.35） | 不可拷贝类型把拷贝构造与拷贝赋值一起 = delete，因为只删一个另一个仍可用（C.21）
TABLE: 工具对照（工具/开关 × 查什么 × 何时跑）与写法选型（场景 × 写法 × 规则号）
