# Chapter 1: 所有权与生命周期（Ownership & Lifetime）

## Core Idea

每块内存必须有且只有一个明确的"主人"（owner），职责是在自己活着时释放它。把释放绑到作用域与对象生命周期上——即 RAII（Resource Acquisition Is Initialization，资源获取即初始化）——就消灭了绝大多数内存 bug。动手前先答"这块内存谁负责释放"：不是"用完 delete"，而是"属于哪个对象 / 作用域"。

## Frameworks Introduced

- **RAII（资源获取即初始化）**
  - When to use: 任何"获取—持有—释放"的资源：内存、文件句柄、锁、socket、事务。
  - How: 构造获取、析构释放；提前 `return` 或抛异常靠栈展开（stack unwinding）保证析构照样执行（E.6、R.1）。
- **智能指针选型（指针 = 借用，智能指针 = 拥有）**
  - When to use: 决定一个值由值语义还是智能指针承载。
  - How: 裸 `T*` / `T&` 永不拥有（R.3、R.4）；`unique_ptr` 唯一拥有（R.20），`shared_ptr` 共享拥有（R.21），`weak_ptr` 只观察、不延长寿命（R.24）。共享前先问"多方都可能最后释放吗"——是 → `shared_ptr`（先看能否改成 `unique_ptr` + 明确的"管理者"），否 → `unique_ptr`（默认答案）。
- **Rule of Zero / Rule of Five（零法则 / 五法则）**
  - When to use: 类里含持有资源的成员。
  - How: 零法则优先——成员自己管好，你什么都不写；确需自定义才退到五法则，拷贝 / 移动 / 析构要么全写要么全 `= delete`（C.21）；多态类另需抑制 public copy/move（C.67），否则派生类对象经基类值传递会被切片。

## Key Concepts

- **所有权（ownership）**：资源在语义上归谁释放；必须显式可判读，不靠口头约定。
- **借用（borrowing）**：拿到指向别人资源的指针或引用，不负释放责任、不延长寿命（R.3、R.4）。
- **RAII（Resource Acquisition Is Initialization）**：构造获取、析构释放；异常路径靠栈展开（stack unwinding）逐层调用析构。
- **唯一 / 共享所有权**：`unique_ptr` 不可拷贝只能移动；`shared_ptr` 计数归零才销毁。
- **弱观察（weak observation）**：`weak_ptr` 不参与计数，`lock()` 时才临时提升，专治环引用。
- **悬垂（dangling）**：指针或引用仍指向已析构 / 已移走的对象，访问即 UB（UAF）。
- **有效但未指定状态（valid but unspecified state）**：移动后的源对象可析构、可重新赋值，但值不可依赖（C.64）。

## Mental Models

- 把 `unique_ptr` 想成**唯一一张房产证**：可转手（移动），不能复印（拷贝）。
- 把 `shared_ptr` 想成**多人共有 + 一本计数簿**：最后一个离开才拆房；两人互相"登记对方为共有权人"，房子永远拆不掉。
- 把 `weak_ptr` 想成**只登记地址不登记人名**的访客名单：能查地址，房子拆了也不阻拦——破环就靠这条边。
- 把 RAII 想成**作用域是一张自动兑现的保险单**：离开作用域＝兑现释放，与你走到底、提前 `return` 还是抛异常无关。

## Anti-patterns

- **返回局部对象的引用或指针**：局部对象已析构，引用立刻悬垂（F.43）；改按值返回，让 RVO/移动处理。
- **lambda 按引用捕获局部变量或捕获 `this`**：捕获对象活得比 lambda 短即 UAF；非局部使用的 lambda 一律按值捕获（F.53、F.54）。
- **`shared_ptr` 循环引用**：互相持有使计数永不归零；一条边改 `weak_ptr`（R.24）。
- **显式 `new` / `delete`**：分配与接管分两步，中间抛异常就泄漏（R.11、R.12）；改 `make_unique` / `make_shared`（R.22、R.23）。
- **用智能指针表达"借用"**：入参默认 `T&` / `T*`（F.7）；要接管才用 `unique_ptr`（R.32），要共享才用 `shared_ptr`（R.34）。
- **移动操作不标 `noexcept`**：`vector` 扩容时只有移动可能抛异常才退回复制（C.66）。

## Code Examples

```cpp
class File {
public:
    explicit File(const char* path) : fp_(std::fopen(path, "rb")) {
        if (!fp_) throw std::runtime_error("open failed");
    }
    ~File() { std::fclose(fp_); }   // 无论怎么退出，句柄都会释放
private:
    std::FILE* fp_;
};

void process() {
    File f("data.bin");              // 进入作用域：获取
    if (some_error()) return;        // 提前返回：析构照样执行
    throw std::logic_error("boom");  // 抛异常：栈展开时析构照样执行
}
```

- **What it demonstrates**: RAII 一条路径覆盖"正常结束 / 提前 return / 抛异常"，释放不依赖调用方记得 `fclose`。
- **签名上的借用 vs 拥有**：`void draw(const Shape&);` 纯借用，`void draw(Shape&);` 可改但不拥有，`std::unique_ptr<Canvas> make_canvas();` 转移所有权（F.26）。

## Reference Tables

**所有权铁律（Core Guidelines）**

| 规则 | 含义 |
|---|---|
| **R.11** | 不显式 `new` / `delete`；用 RAII 资源句柄。 |
| **R.20** | 用 `unique_ptr` 或 `shared_ptr` 表示所有权。 |
| **R.21** | 除非确需共享，优先 `unique_ptr` 而非 `shared_ptr`。 |
| **R.24** | 用 `std::weak_ptr` 打破 `shared_ptr` 的循环。 |

**所有权类型速查**

| 类型 | 语义 | 拷贝 | 移动 | 典型用途 |
|---|---|---|---|---|
| `T` | 值语义，自有一切 | 深拷贝 | 移动 | 常规数据 |
| `T*` / `T&` | 不拥有，**借用** | 复制指针 | 复制指针 | 传参、观察者 |
| `std::unique_ptr<T>` | **唯一**所有者 | ✗ 不可拷贝 | ✓ | 默认选择 |
| `std::shared_ptr<T>` | **共享**所有权 | ✓（计数+1） | ✓ | 确有共享场景 |
| `std::weak_ptr<T>` | 观察者，不延长寿命 | ✓ | ✓ | 打破循环 / 缓存 |

## Worked Example

**场景**：`widget.h` 暴露 `static Widget* create(int id);`，内部 `new`，调用方自己 `delete`。所有权靠口头约定 → 有人漏 delete，有人 double delete。

**Step 1 — 定位缺口。** 全量搜 `create(` 的调用点，逐个回答"谁 delete"；答案不一致处就是泄漏点。评审别问"记得 delete 吗"，要问"这个指针归谁"。

**Step 2 — 所有权写进签名。** 返回类型改成 `std::unique_ptr<Widget>`（R.20、F.26），调用方拿到"主人"身份；实现里用 `make_unique`（R.23），消除"裸 new 与接管分两步、中间抛异常"的窗口（R.11、R.12）；借用参数 `void apply(Widget* w)` 改为 `void apply(const Widget& w)`，让"不延长生命周期"写在类型里（F.7）。

```cpp
// ===== ✗ 改造前：所有权靠约定 =====
class Widget {
public:
    static Widget* create(int id) { return new Widget(id); }  // 谁 delete？靠调用方猜
};
void use() {
    Widget* w = Widget::create(42);
    if (!w) return;
    render(w);          // 借用
    delete w;           // 提前 return 或中途抛异常 → 泄漏
}

// ===== ✓ 改造后：所有权写进签名 =====
class Widget {
public:
    static std::unique_ptr<Widget> create(int id) {
        return std::make_unique<Widget>(id);   // 分配 + 接管一步完成
    }
};
void use() {
    auto w = Widget::create(42);   // 拿到的就是"主人"身份
    if (!w) return;
    render(*w);                    // 借用用引用，不延长生命周期
}                                  // 无论怎么退出，w 自动析构
```

- **What it demonstrates**: 所有权从"注释里的一句话"变成"类型里的事实"，编译期就能看出谁负责释放。

**Step 3 — 清掉悬垂与环。** 返回局部对象的引用一律改按值返回（F.43；C++26 起 P2266 "Simpler implicit move" 让隐式移动更彻底）；双向链表的 `shared_ptr` 环把一条边改 `weak_ptr`（R.24）。

**结果**：调用方从 `Widget* w = ...; ... delete w;` 变成 `auto w = ...;`，少一处可能写错的 `delete`。验收：ASan/LSan 跑全量用例，leak 为 0；编译期检查确认无裸 `new`/`delete` 残留（R.11）。

## Key Takeaways

1. 动手前先答"这块内存谁负责释放"：答案必须是"属于哪个对象 / 作用域"，不是"用完 delete"。
2. 默认 `unique_ptr`；真有"多方都可能最后释放"才用 `shared_ptr`（R.21），环用 `weak_ptr` 破（R.24）。
3. 借用用 `T&` / `T*` 表达（F.7、R.3、R.4），拥有用智能指针；绝不返回局部对象的指针或引用（F.43），也不返回 `T&&`（F.45）。
4. 优先 `make_unique` / `make_shared`（R.22、R.23）；确需裸 `new` 立刻交给管理对象（R.12）。
5. lambda 离开创建它的作用域就按值捕获，绝不捕获 `this`（F.53、F.54）；移动操作标 `noexcept`（C.66）。
6. 用 `-Wall -Wextra -Wpedantic -Werror` 加 ASan/LSan 兜底——泄漏和 UAF 交给工具报，不靠人眼。

## Connects To

- **Ch02**: 所有权如何转移 —— `unique_ptr` 的移动构造 / 移动赋值是"唯一拥有"的完整规则。
- **Ch04**: 容器的所有权模型 —— `vector` / `map` 的元素所有权、扩容时的移动代价与迭代器失效。
- **Ch05**: 跨线程共享所有权 —— `shared_ptr` 引用计数的原子性；真正要加锁的是数据不是指针。
- **Ch06**: 异常路径上的资源释放 —— E.6 的落地细节：栈展开、`final_action`（E.19）、析构不得抛异常（C.37、E.16）。
- **Ch11**: 悬垂引用等生命周期陷阱 —— F.43 / F.53 的完整反例库与 Sanitizer 检测手段。

### EXTRACT ch01
TERMS: 所有权（ownership） | 借用（borrowing） | RAII（Resource Acquisition Is Initialization） | 唯一所有权（unique ownership） | 共享所有权（shared ownership） | 弱观察（weak observation） | 悬垂（dangling） | 有效但未指定状态（valid but unspecified state）
PATTERNS: RAII 资源句柄（何时用：持有文件句柄、锁、socket、事务等任何需要释放的资源；做法：构造获取、析构释放，绝不手写 delete） | 所有权智能指针（何时用：堆上对象必须明确主人；做法：默认 make_unique，确实共享才 make_shared，成环用 weak_ptr 破） | 签名表达借用 vs 拥有（何时用：写函数接口时；做法：借用用 T&/T*，接管用 unique_ptr 或 X&& + std::move）
DECISIONS: 当资源要不要共享时选 unique_ptr 而非 shared_ptr，因为共享需要显式理由且默认答案就是唯一拥有（R.21） | 当返回对象时选按值而非返回引用，因为返回局部对象的引用必然悬垂（F.43） | 当捕获 lambda 时选按值而非按引用，除非能确认被捕获对象活得比 lambda 久（F.53）
TABLE: 所有权类型（T / T* / unique_ptr / shared_ptr / weak_ptr）× 语义、拷贝、移动、典型用途
