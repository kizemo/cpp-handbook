# Chapter 7: 性能优化（Performance Optimization）

## Core Idea

先测量，再优化：没有 profiler 数据支撑的"优化"，90% 是把代码改慢而不是改快（Per.1、Per.2、Per.6）。确认是瓶颈之后，优化顺序也是固定的——先改算法复杂度，再动常数因子。

## Frameworks Introduced

- **不可跳步的优化流程（Measure → Locate → Change → Re-measure → Test → Record）**：六步闭环，缺一步优化就无法验证。
  - When to use: 任何"这里可能慢"的念头出现时，尤其是已经有人准备动手改代码时。
  - How: 测基线 → 找瓶颈（`perf` / VTune / Instruments，不靠猜）→ 只改一处 → 再测量 → 跑测试 → 记录原因（Per.6、Per.7）。
- **优化优先级阶梯（Optimization priority ladder）**：算法复杂度 → 缓存与数据布局 → 内存分配次数 → 移动代替拷贝 → 分支预测 → 编译期计算 → 构建配置。
  - When to use: 已确认热点、准备决定"先动哪一层"时。
  - How: 复杂度的量级差异远大于任何常数因子优化——一个 O(n²) 循环优化 50% 还是 O(n²)，换成哈希集合才是 O(n)（Per.3、Per.4、Per.5）。
- **可信 benchmark 三要素（Fixed seed + DoNotOptimize + 多档规模）**：让基准数字站得住。
  - When to use: 需要为任何性能改动提供证据时。
  - How: 固定种子生成可复现输入；`DoNotOptimize` 防止编译器把被测结果优化掉；多档规模看伸缩曲线而不是单点（Per.6）。
- **常数因子优化的六种手段（Move / Reserve / SSO / Cache-friendly / Branch-friendly / Compile-time）**：复杂度已到位后的具体抓手。
  - When to use: profile 显示热点仍占大头，且算法已没有更优解时。
  - How: 移动代替拷贝、`reserve` 预留容量、`string_view` 绕开堆分配、连续数组换链表、分支改查表、`constexpr`/`consteval` 移到编译期（Per.11、Per.14、Per.16、Per.19）。
- **伪共享隔离（False-sharing isolation）**：用对齐或 padding 把互相踩踏的写者分开。
  - When to use: 多个写者写同一 cache line 上的不同变量，profile 显示缓存失效异常时。
  - How: `alignas(64)` 或 padding 把热点变量分到不同缓存行（Per.18、Per.19）。

## Key Concepts

- **基线（baseline）**：改动前在固定构建配置下测出的参照数字；没有基线就无从判断"变快了"。
- **瓶颈定位（bottleneck localization）**：用采样型 profiler 找出耗时集中处，而不是靠直觉猜（Per.6）。
- **复杂度量级（complexity order）**：O(n²)、O(n log n)、O(n) 之间的差距是乘性的，不是加性的。
- **常数因子（constant factor）**：不改变复杂度级别、只降低每次操作代价的那部分优化空间。
- **SSO（small string optimization，小字符串优化）**：`std::string` 对短字符串（通常 ≤15 字符）不做堆分配；热路径上换成 `std::string_view` 或固定数组能省掉分配。
- **缓存友好性（cache friendliness）**：数据布局是否让 CPU 预取器和缓存行用得上；往往比算法常数更重要（Per.16、Per.19）。
- **AoS / SoA（array of structs / struct of arrays）**：结构体数组适合顺序整体访问，字段数组适合只访问部分字段。
- **分支预测友好（branch-predictable）**：可预测分支近乎免费，不可预测分支每次都要冲刷流水线。
- **伪共享（false sharing）**：多个写者写同一缓存行上的不同变量，缓存一致性来回失效，性能暴跌。

## Mental Models

- 把优化当"实验"而不是"改造"：基线是对照组，一次只改一个变量，改完必须重测（Per.6）。
- 把复杂度当"数量级"、常数因子当"零头"：先换量级再抠零头，别一上来就抠指令级细节（Per.4、Per.5）。
- 把 benchmark 当"实验装置"：固定种子 = 输入不漂移，`DoNotOptimize` = 被测对象不被优化掉，多档规模 = 能看伸缩而不是单点。
- 把内存访问当"要交过路费"：每次跨缓存行都要问一句，这行数据是不是已经在手上（Per.18、Per.19）。

## Anti-patterns

- **凭直觉说"`vector` 比 `list` 快"**：可能对，但理由是缓存而非复杂度；拿数据说话（Per.6）。
- **手写循环替代标准算法**：标准算法往往已被优化过，而且更安全（Per.5）。
- **用位运算替代算术**：可读性代价巨大，除非 profile 证明有效（Per.5）。
- **过早引入缓存层**：缓存失效 bug 比性能收益更难修。
- **为了减少拷贝而牺牲正确性**：永远不值。
- **benchmark 不加 `DoNotOptimize`**：编译器把结果优化掉，测出 0.01ns 的假数据（Per.6）。
- **在 `-O0` 下测性能**：测的是 debug 版本，结论对发布版无效。
- **一次改多处**：测不出是哪一处生效，下次只能整体回退（Per.7）。
- **跳过复杂度直奔微优化**：顺序反了——先把 O(n²) 换成 O(n)，再谈常数。

## Code Examples

```cpp
// ✗ 每次 push_back 都拷贝一遍字符串
void add(std::vector<std::string> v, const std::string& s) { v.push_back(s); }
// ✓
void add(std::vector<std::string>& v, std::string s) { v.push_back(std::move(s)); }

std::vector<int> v;
v.reserve(10000);            // ✓ 一次分配，零扩容
v.shrink_to_fit();           // 结束后收缩（注意：这本身也有成本）
```

- **What it demonstrates**: 按值接收入参 + `std::move` 把拷贝变移动；`reserve` 把多次分配压成一次（Per.14）。

```cpp
// ✗ 链表：节点分散，缓存命中率低
std::list<Node> nodes;

// ✓ 连续数组：CPU 预取器能工作
std::vector<Node> nodes;

// C++17 起用 alignas 隔离缓存行，避免伪共享
alignas(64) std::array<std::byte, 64> cache_line;
```

- **What it demonstrates**: 节点分散的代价来自缓存而不是复杂度；`alignas` 把互相踩踏的写者分开（Per.16、Per.18、Per.19）。

```cpp
constexpr int fib(int n) { return n < 2 ? n : fib(n-1) + fib(n-2); }
static_assert(fib(10) == 55);      // 编译期求值，零运行时开销

consteval int square(int x) { return x * x; }
// constexpr auto a = square(4);   // ✓
```

- **What it demonstrates**: 把计算从运行期移到编译期；C++20 的 `consteval` 强制编译期求值（Per.11）。

## Reference Tables

### 优化优先级表

| 优先级 | 手段 | 层级 | 判据 / 收益 |
|---|---|---|---|
| P0 | 证明是瓶颈（基线 + profiler） | 流程 | 没有数据不动手；跳过这步多数是负收益（Per.1、Per.2、Per.6） |
| P1 | 换算法与数据结构 | 复杂度 | O(n²) 改一半仍是 O(n²)，换哈希集合才是 O(n)（Per.3） |
| P2 | 数据布局与缓存友好性 | 常数因子（常比其它常数因子更重要） | 连续数组 vs 链表；AoS vs SoA（Per.16、Per.19） |
| P3 | 减少分配次数 | 常数因子 | `reserve`、SSO／`string_view`、缓冲复用、池化（Per.14、Per.15） |
| P4 | 移动代替拷贝 | 常数因子 | `std::move` 接管入参与容器元素（Per.14） |
| P5 | 分支预测友好 | 常数因子 | 不可预测分支改查表（适合密集数据） |
| P6 | 编译期计算 | 常数因子 | `constexpr` / `consteval`（Per.11） |
| P7 | 构建配置 | 配置（非代码改动） | `-O2`/`-O3`、`-march=native`、LTO、PGO（Per.4） |

### 常数因子手段对比表

| 手段 | 适用场景 | 做法 | 注意 |
|---|---|---|---|
| 移动代替拷贝 | 大对象频繁传入或装入容器 | 按值接收 + `std::move` | 移动后源对象只保证"有效但未指定" |
| 预留容量 | 已知元素数量 | `reserve(n)` | 多预留是浪费内存 |
| 小对象优化（SSO） | 热路径上的短字符串 | 换 `std::string_view` 或固定数组 | `string_view` 是借用，不拥有数据 |
| 缓存友好性 | 顺序遍历大量数据 | 连续数组优先；必要时 AoS → SoA | 换容器会改语义，先查迭代器失效 |
| 分支预测友好 | 密集数据的分类处理 | 查表替代不可预测分支 | 只在 profile 指向分支时才做 |
| 编译期计算 | 结果固定的计算 | `constexpr` / `consteval` | 运行期才拿得到的值编译期算不了 |

### benchmark 陷阱表

| 陷阱 | 后果 |
|---|---|
| 编译器把整个循环优化掉 | 测出 0.01ns 的假数据 |
| 没开优化等级 | 测的是 debug 版本 |
| 输入数据太单一（全是同一个值） | 分支预测器全命中，虚高 |
| 缓存全热 | 测的是 L1 命中而非真实场景 |
| 每次迭代都分配内存 | 测的是分配器性能 |
| 样本太少 | 被噪声主导 |

## Worked Example

**场景**：热路径上的 `contains_dup()` 被抱怨"太慢"，但没人给得出数字；同一条路径上还有一个每帧都在 `push_back` 字符串的 `add()`。

**步骤 1｜先把测量装置修对**。在 `-O0` 下测等于测 debug 版；不加 `DoNotOptimize` 会让编译器把结果删掉、测出 0.01ns；只用单一输入则分支预测全命中。按"固定种子 + `DoNotOptimize` + 多档规模"建基线：

```cpp
static void BM_Dedup(benchmark::State& state) {
    std::vector<int> data(state.range(0));
    for (int i = 0; i < state.range(0); ++i) data[i] = (i * 2654435761u) % 100000;
    for (auto _ : state) {
        auto dup = contains_dup(data);
        benchmark::DoNotOptimize(dup);
    }
}
BENCHMARK(BM_Dedup)->Range(1 << 10, 1 << 20);
```

**步骤 2｜定位瓶颈**。`perf record` 采样显示 `contains_dup` 占总时长的大头，其余是 I/O——优化对象明确，不靠猜。

**步骤 3｜按优先级一刀一刀切，每刀只改一处、改完重测**。

第一刀（复杂度）：原实现是双重循环 O(n²)，换成哈希集合：

```cpp
// ✗ O(n²)
bool contains_dup_slow(const std::vector<int>& v) {
    for (std::size_t i = 0; i < v.size(); ++i)
        for (std::size_t j = i + 1; j < v.size(); ++j)
            if (v[i] == v[j]) return true;
    return false;
}

// ✓ O(n)
bool contains_dup(const std::vector<int>& v) {
    std::unordered_set<int> seen;
    for (int x : v) {
        if (!seen.insert(x).second) return true;
    }
    return false;
}
```

量级差异远大于任何常数因子优化：一个 O(n²) 循环优化 50% 还是 O(n²)。重测后把两档规模的数字贴出来。

第二刀（分配次数）：`add()` 每次 `push_back` 都拷贝一遍字符串——改成按值接收入参 + `std::move`，并 `reserve` 掉容量（Per.14）。同时确认热路径遍历的是连续数组而不是节点分散的链表；只访问部分字段时再考虑 SoA（Per.16、Per.19）。

第三刀（构建配置）：代码层面到头之后，才动 `-O2`/`-O3`、`-march=native`、LTO、PGO——这些是构建配置而不是代码改动（Per.4）。

**步骤 4｜跑测试**，确认优化没有改坏行为。

**步骤 5｜记录**：把"改前改后的基准数字 + 为什么这么改（O(n²) → O(n)，profile 显示热点在此）"写进提交信息，防止后人"优化"回去。

## Key Takeaways

1. 先测量再优化；没有 profiler 数据支撑的优化，90% 是把代码改慢而不是改快（Per.1、Per.2、Per.6）。
2. 优化顺序固定：算法复杂度 → 缓存与数据布局 → 分配次数 → 移动代替拷贝 → 分支预测 → 编译期计算 → 构建配置。
3. 一个 O(n²) 循环优化 50% 还是 O(n²)；量级差异远大于任何常数因子。
4. 复杂度到位后再抠常数因子：`reserve`、SSO／`string_view`、缓冲复用、AoS／SoA、查表替分支。
5. 可信基准的最低要求：固定种子 + `DoNotOptimize` + 多档规模，而且永远在 `-O2` 以上测。
6. 编译器选项是构建配置不是代码改动；不要为跑分牺牲可维护性（Per.4、Per.5）。
7. 每次只改一处、改完重测，并记录"为什么这么改"。

## Connects To

- **Ch05**: 伪共享与关键路径开销 —— 缓存行争用（Per.19）和上下文切换（Per.30、CP.43）是并发场景下两类"隐形性能税"。
- **Ch11**: 性能类陷阱 —— "看起来更快"的手写循环、`auto` 吃掉移动、迭代器失效，属于同一类"直觉骗人"的坑（Per.5、Per.6）。
- **Ch10**: 工具链 —— `perf`、`valgrind --tool=callgrind`、`heaptrack` 与 sanitizer 是"先测量"这条纪律的落地工具；完整的工具对照表见该章。
- **Ch04**: 容器与算法 —— `unordered_*` 的负载因子与 `reserve` 决定是否退化成 O(n)；`vector` 与 `list` 的差距来自缓存而非复杂度（Per.14、Per.19）。
- **`std::string_view`**: 热路径上去掉短字符串的堆分配；借用语义，生命周期由调用方保证。

### EXTRACT ch07
TERMS: 基线（baseline） | 瓶颈定位（bottleneck localization） | 复杂度量级（complexity order） | 常数因子（constant factor） | 小对象优化（SSO, small string optimization） | 缓存友好性（cache friendliness） | AoS/SoA（array of structs / struct of arrays） | 伪共享（false sharing）
PATTERNS: 不可跳步优化流程（何时用：想优化时；做法：基线→profiler 找瓶颈→只改一处→再测→跑测试→记录原因） | 优化优先级阶梯（何时用：已确认热点；做法：复杂度→缓存布局→分配次数→移动代替拷贝→分支预测→编译期计算→构建配置） | 可信 benchmark 三要素（何时用：为性能改动举证；做法：固定种子 + DoNotOptimize + 多档规模，且在 -O2 以上测）
DECISIONS: 当 O(n²) 热路径出现时先换算法，因为量级差异远大于常数因子优化 | 当算法已无更优解才动常数因子，因为顺序反了会白花力气 | 当 benchmark 数字异常快时不采信，因为编译器可能把结果优化掉了
TABLE: 优化优先级 vs 手段——行是 P0–P7 阶梯，列是手段、层级（复杂度/常数因子/配置）、判据与收益
