# Chapter 4: STL 容器与算法（STL Containers & Algorithms）

## Core Idea

默认 `vector`、默认标准算法、默认假设"迭代中容器可能被改过"：选型与迭代器失效是设计输入，不是事后才暴露的 bug。

## Frameworks Introduced

- **容器选型决策树**：有序 → `map`／`set`；不要序 → `unordered_*`；连续 → `vector`；两端插删 → `deque`；少而固定 → `array`／`span`。
  - When to use: 新增容器字段、返回值或参数类型时。
  - How: 先写 `vector`，等 profiler 证明是瓶颈再换；`unordered_*` 已知规模就 `reserve` + `max_load_factor`（SL.con.2、Per.1、Per.14）。
- **算法优先（Algorithm-first）**：标准库算法经得起所有边界条件检验。常用：`sort`／`find_if`／`count_if`／`transform`。
  - When to use: 遍历、查找、排序、转换、聚合逻辑。
  - How: 先找算法；谓词表达筛选、投影表达按成员比较（T.40、ES.1、ES.3）。
- **erase-remove 惯用法（Erase-remove idiom）**：`std::remove`／`remove_if` 只把待删元素移到尾部，**不改变大小**；删除必须配 `erase`，C++20 起用 `std::erase_if`。
  - When to use: 按条件批量删除元素。
  - How: `v.erase(std::remove_if(v.begin(), v.end(), pred), v.end());`
- **迭代器失效规则与安全迭代方案**：失效规则见下方速查表；安全改法有三。
  - When to use: 审查"迭代中修改容器"的代码。
  - How: ① 先收集再插入；② 用下标，每轮重算 `v.size()`；③ `for (auto x : v)` 迭代副本（`auto&` 引用仍会失效）。

## Key Concepts

- **迭代器失效（iterator invalidation）**：结构变化后旧迭代器／引用不再指向原元素，继续使用即 UB。
- **非拥有视图（non-owning view）**：`span`／`string_view` 只借用数据，不拥有也不延长寿命。
- **擦除-移除（erase-remove）**：把"筛选元素"与"改变大小"拆成两步的惯用法。
- **谓词与投影（predicate & projection）**：谓词表达筛选条件，投影指定算法作用于哪个成员。
- **负载因子（load factor）**：哈希表元素数与桶数之比；越小冲突越少、占内存越多。

## Mental Models

- 把 `vector` 当"默认答案"：先按默认写，等测量证明它是瓶颈再换（SL.con.2、Per.2）。
- 把迭代器当"容器内部的裸指针"：会触发重新分配的操作，让旧指针指向已释放的内存。
- 把 `std::remove` 当"整理员"而不是"删除器"：它只重排，缩短容器的权限在 `erase` 手里。

## Anti-patterns

- **手写循环代替标准算法**：边界条件与重复代码由你长期维护（ES.1、ES.3）。
- **`std::remove` 忘了 `erase`**：元素只是被挪到尾部，`size()` 没变。
- **遍历中 `push_back` 却用旧迭代器**：可能触发重新分配，旧迭代器悬垂——是 UB。
- **默认用 `list`**：节点分散在堆上，缓存命中率极低，现代 CPU 上几乎总是更慢。
- **`string_view` 指向临时 `std::string`**：临时对象销毁即悬垂；拥有数据用 `std::string`（SL.str.1、SL.str.2、F.43）。
- **用 `T arr[]` 参数代替 `span`**：丢失长度、允许越界（SL.con.3、R.14、I.13）。

## Code Examples

```cpp
// ✗ 危险：push_back 可能让迭代器失效
for (auto it = v.begin(); it != v.end(); ++it) {
    if (some_condition(*it)) v.push_back(other);   // it 可能已失效
}

// ✓ 方案 A：先收集再插入
std::vector<Item> to_add;
for (const auto& x : v) if (should_add(x)) to_add.push_back(x);
v.insert(v.end(), to_add.begin(), to_add.end());

// ✓ 方案 B：用下标，每轮重算 v.size()
for (std::size_t i = 0; i < v.size(); ++i)
    if (should_add(v[i])) v.push_back(other);
```

- **What it demonstrates**: 迭代中修改容器的后果与两种安全改法。

```cpp
v.erase(std::remove_if(v.begin(), v.end(), pred), v.end());  // 真正删除
std::erase_if(v, pred);                                     // C++20 起更简洁
```

- **What it demonstrates**: `remove_if` 只重排元素，删除由 `erase` 完成。

## Reference Tables

### 容器选型速查

| 容器 | 底层 | 随机访问 | 插入/删除 | 查找 | 典型场景 |
|---|---|---|---|---|---|
| `vector` | 连续数组 | ✅ O(1) | 尾部 O(1)，中间 O(n) | O(n) | **默认首选** |
| `deque` | 分段数组 | ✅ O(1) | 两端 O(1) | O(n) | 双端队列 |
| `list` | 双向链表 | ❌ | 已知位置 O(1) | O(n) | 极少用（缓存不友好） |
| `map` | 红黑树 | ❌ | O(log n) | O(log n) | **有序**键值对 |
| `set` | 红黑树 | ❌ | O(log n) | O(log n) | 有序去重集合 |
| `unordered_map` | 哈希表 | ❌ | 平均 O(1) | 平均 O(1) | **无序**键值对 |
| `array` | 定长数组 | ✅ O(1) | 编译期 | O(n) | 固定小尺寸 |
| `span` / `string_view` | 视图 | ✅ | — | — | 非拥有引用 |

### 迭代器失效速查

| 操作 | 失效的迭代器/引用 |
|---|---|
| `vector::push_back` / `emplace_back` | **全部**（可能触发重新分配） |
| `vector::insert` / `erase` | 插入点及其后全部；`erase` 则是被删位置及其后 |
| `vector::clear` / `resize` 缩小 | 全部 |
| `deque` 在**中间**插入 | 全部；两端插入只失效迭代器，引用仍有效 |
| `list` / `forward_list` | 只有被删除的那个 |
| `map` / `set` / `unordered_*` | 只有被删除的那个（`erase` 不失效其他） |
| `unordered_*` 的 `rehash` | 全部（但引用不失效） |

## Worked Example

**场景**：日志聚合器处理 `LogEntry`（`level`／`user_id`／`city`）：① 筛出 ERROR 记录；② 给 ERROR 记录补全缺失的 `city`。

**步骤 1｜选容器**：保留顺序 → `std::vector<LogEntry>`；只读接口 → `std::span<const LogEntry>` 而非 `const LogEntry[]`（R.14、SL.con.3）。

**步骤 2｜错误版本（两个坑叠在一起）**：

```cpp
for (auto it = all.begin(); it != all.end(); ++it) {
    if (it->level == "ERROR") {
        errors.push_back(*it);
        all.push_back(*it);      // ← 可能重新分配 → it 失效 → 下一轮 ++it 是 UB
    }
}
std::remove_if(all.begin(), all.end(), is_not_error);  // ← 只重排，不删
```

**步骤 3｜正确版本**：

```cpp
all.erase(std::remove_if(all.begin(), all.end(),
                          [](const LogEntry& e) { return e.level != "ERROR"; }),
          all.end());                                    // ① 按条件删除

std::vector<LogEntry> to_add;
for (const auto& e : all)
    if (e.level == "ERROR" && e.city.empty()) to_add.push_back(make_entry(e));
all.insert(all.end(), to_add.begin(), to_add.end());     // ② 先收集再插入
```

**步骤 4｜验证**：`all.size()` 只在 ① 后减少；`errors.size()` 等于 ERROR 条数；ASan 跑一遍，步骤 2 报 heap-use-after-free，步骤 3 干净。

## Key Takeaways

1. 默认 `vector`，等测量证明它是瓶颈再换（SL.con.2、Per.1、Per.2）。
2. 写循环前先找标准算法，谓词用 lambda（ES.1、ES.3、T.40）。
3. `std::remove` 后必须跟 `erase`；C++20 起用 `std::erase_if`。
4. 改容器前先查失效表：`push_back` 让全部迭代器失效。
5. `span`／`string_view` 是借用，绝不能比它指向的数据活得久（SL.str.1、F.43、R.4）。
6. `unordered_*` 已知规模就 `reserve` + `max_load_factor`（Per.6、Per.14）。

## Connects To

- **Ch11**: API 误用与迭代器失效 —— `std::remove` 不删元素、`string_view` 悬垂、迭代器失效都是同类陷阱。
- **Ch03**: 模板与分配器 —— 容器与算法的通用性来自模板（T.3）；`std::less<>` 避免类型擦除的额外间接调用（T.49）。
- **Ch01**: 容器的所有权模型 —— value 语义容器拥有元素，`span`／`string_view` 是非拥有借用（R.3、R.4）。
- **Ch07**: 哈希容器性能 —— 哈希质量与负载因子决定 `unordered_*` 是否退化（Per.6、Per.14、Per.19）。
