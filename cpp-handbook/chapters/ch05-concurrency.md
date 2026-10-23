# Chapter 5: 并发编程（Concurrency）

## Core Idea

并发的难点不是"怎么加锁"，而是"怎么证明没有数据竞争"（CP.2）。默认单线程；把并发当成需要明确论证的优化手段，而不是起点。

## Frameworks Introduced

- **并发必要性阶梯（Concurrency justification ladder）**：更快的算法/数据结构 → 批处理/缓存/惰性求值 → 单线程异步（事件循环/协程） → 多线程。
  - When to use: 任何"加个线程试试"的冲动出现时。
  - How: 自上而下逐级排除；只有当任务是 CPU 密集且能证明并行收益时才落到多线程（Per.1、Per.2、CP.4）。
- **共享状态最小化（Minimize explicit sharing of writable data）**：能按值传就不共享；必须共享所有权时才上 `shared_ptr`。
  - When to use: 设计线程间接口、给 worker 传输入时。
  - How: 小数据按值传（CP.31）；确需共享所有权用 `shared_ptr`（CP.32、CP.3、R.20）。
- **锁即 RAII（Lock as RAII）**：`std::scoped_lock`／`std::unique_lock`／`std::lock_guard` 取代裸 `lock()`/`unlock()`；多把锁一次性获取。
  - When to use: 任何临界区。
  - How: 锁与被保护的数据放在一起声明（CP.50）；多锁用 `std::scoped_lock`（CP.21）；持锁期间不调用未知代码或回调（CP.22）。
- **Release-Acquire 发布订阅（release-acquire synchronization）**：写侧 `memory_order_release` 发布，读侧 `memory_order_acquire` 订阅，配对建立可见性。
  - When to use: 单写多读，或"先填数据再置标志位"的模式。
  - How: 默认用 `memory_order_seq_cst`；只有测量证明锁是瓶颈时才降级到弱序（CP.101）。
- **带谓词的条件变量（Predicated condition variable）**：等待条件用谓词表达，`cv.wait(lock, pred)`。
  - When to use: 生产者—消费者、任务队列、优雅停机。
  - How: 改状态必须持锁，通知放在解锁之后（CP.42）。
- **线程池（Thread pool）**：固定数量 worker + 加锁的任务队列 + 条件变量。
  - When to use: 任务短、数量大，线程创建销毁本身开始成为瓶颈时。
  - How: 任务队列本身也要加锁；等待必须带谓词；析构时置停止标志 → `notify_all` → `join`（CP.41、CP.40、CP.23）。

## Key Concepts

- **数据竞争（data race）**：两个线程并发访问同一内存位置、至少一个是写、且无同步 → 未定义行为，而不是"读到旧值"（CP.2）。
- **内存序（memory order）**：原子操作允许的重排强度；`seq_cst` 最强也最安全，`relaxed` 只保证原子性、不保证顺序。
- **Release-Acquire 配对**：写侧 release 之前的写、读侧 acquire 之后的读都不会被重排跨越，这是"发布—订阅"的最小充分条件。
- **虚假唤醒（spurious wakeup）**：`wait` 允许在条件未满足时返回；唯一可靠的防御是谓词。
- **临界区与锁粒度（lock granularity）**：持锁时间越短越好，IO、回调、未知代码不放进临界区（CP.43）。
- **死锁（deadlock）**：多线程以不一致顺序获取多把锁而互相等待；`std::scoped_lock` 用死锁避免算法解决（CP.21）。
- **伪共享（false sharing）**：不同线程写同一 cache line 上的不同变量，缓存一致性来回失效，性能暴跌。
- **无锁（lock-free）**：保证系统整体能前进的并发结构；不等于更快，内存序推理成本极高（CP.100）。
- **线程安全（thread safety）**：对象在并发访问下不产生数据竞争且行为可预测；标准库容器本身不提供内部同步。

## Mental Models

- 把 `std::mutex` 当"数据的附属字段"：谁保护什么，锁就和数据声明在同一个地方（CP.50）。
- 把 release/acquire 当"两端的栅栏"而不是"全局屏障"：release 之后的写不许提前，acquire 之前的读不许推后；不需要全局总序就别上 `seq_cst`。
- 把条件变量当"门铃"而不是"邮箱"：门铃可能按错人、也可能干脆没按响，状态的真相只存在于谓词里（CP.42）。
- 把 `std::thread` 当"作用域容器"：出了作用域必须 join（CP.23）；能 `detach` 的地方几乎都不该 `detach`（CP.26）。

## Anti-patterns

- **`volatile` 当同步用**：`volatile` 不是原子操作、没有内存序保证，它只用来和 C++ 内存模型之外的硬件寄存器说话（CP.8、CP.200）。
- **手写 `lock()`/`unlock()`**：异常或提前返回时锁不会释放；一律用 RAII 锁类型（CP.20）。
- **多锁不用 `std::scoped_lock`**：两把以上锁获取顺序不一致即死锁（CP.21）。
- **持锁时调用未知代码（回调、插件、IO）**：对方可能反过来拿同一把锁 → 死锁或优先级反转（CP.22）。
- **`detach()` 后线程访问栈上对象**：主线程返回即悬垂；改用 `join` 或 C++20 的 `std::jthread`（CP.26、CP.24）。
- **条件变量 `wait` 不带谓词**：虚假唤醒直接变成逻辑错误（CP.42）。
- **临界区里做 IO 或重计算**：锁竞争被放大；先取快照再干慢活（CP.43）。
- **原子用 `memory_order_relaxed` 做发布/订阅**：可见性毫无保证，且极难排查（CP.101）。
- **手写无锁数据结构**：复杂度、ABA 问题、伪共享全部自己扛；先用 `folly`／`boost::lockfree`（CP.100、CP.102）。
- **协程跨挂起点持有锁**：挂起期间锁仍被占，其它线程全部卡死（CP.52）。

## Code Examples

```cpp
#include <atomic>

int counter = 0;                      // 普通变量
void unsafe_inc() { ++counter; }      // ✗ 数据竞争 → 未定义行为（CP.2）

std::atomic<int> safe_counter{0};     // 原子变量
void safe_inc() { ++safe_counter; }   // ✓ 原子操作
```

- **What it demonstrates**: 数据竞争的判定条件——同一地址、并发、至少一个写、无同步。

```cpp
std::atomic<bool> ready{false};
int data = 0;

void producer() {
    data = 42;
    ready.store(true, std::memory_order_release);   // 发布
}
void consumer() {
    while (!ready.load(std::memory_order_acquire)) {}
    // 此处读到的 data 一定可见
    use(data);
}
```

- **What it demonstrates**: Release-Acquire 配对如何把"写数据"和"置标志"合成一个可见性保证。

```cpp
std::mutex mtx;
std::condition_variable cv;
bool ready = false;

void wait_for_ready() {
    std::unique_lock lock(mtx);
    cv.wait(lock, []{ return ready; });     // ✓ 带谓词，防虚假唤醒
}

// 通知方：先持锁改状态，解锁后再通知
{
    std::scoped_lock lock(mtx);
    ready = true;
}
cv.notify_one();
```

- **What it demonstrates**: 等待条件必须由谓词表达，通知只是"门铃"，不是"邮箱"。

```cpp
// ✗ 锁住太多：把 IO 也圈在临界区里
{
    std::scoped_lock lock(mtx);
    data = compute();
    write_to_disk();            // 慢操作，不该持锁
}

// ✓ 只锁数据访问
auto snapshot = [&]{
    std::scoped_lock lock(mtx);
    return data;
}();
write_to_disk(snapshot);
```

- **What it demonstrates**: 锁粒度的取舍——临界区里只留数据访问，慢操作放在锁外（CP.43）。

## Reference Tables

### 内存序速查

| 内存序 | 保证 | 用途 |
|---|---|---|
| `memory_order_relaxed` | 只保证原子性，不约束顺序 | 计数器、统计 |
| `memory_order_consume` | 实践中几乎等同 acquire | 极少用 |
| `memory_order_acquire` | 之后的读写不能重排到它之前 | 读侧，配对 release |
| `memory_order_release` | 之前的读写不能重排到它之后 | 写侧，配对 acquire |
| `memory_order_acq_rel` | 读-改-写操作 | `fetch_add` 等 |
| `memory_order_seq_cst` | 全局单一顺序（默认，最强） | 不确定时的安全选择 |

### 互斥锁家族

| 类型 | 特点 |
|---|---|
| `std::mutex` | 不可递归，不可移动 |
| `std::recursive_mutex` | 同一线程可重复加锁 |
| `std::timed_mutex` | 支持 `try_lock_for` |
| `std::scoped_lock` | **C++17 推荐**：一次锁多把，无死锁风险 |
| `std::unique_lock` | 可加锁／解锁／延迟解锁／移动，最灵活 |

### 异步取值设施

| 设施 | 用途 |
|---|---|
| `std::async` | 最简单的一次性异步任务（CP.61） |
| `std::promise` / `std::future` | 手动 set/get 的单值通道（CP.60） |
| `std::packaged_task` | 可复用的任务封装 |
| `std::shared_future` | 多个消费者共享同一结果 |

## Worked Example

**场景**：日志聚合器要处理 N 万条 `LogEntry`（含 `level`、`user_id`、`payload`），对 `payload` 做 CPU 密集的解析（JSON + 正则），并统计各级日志数量。要求吞吐至少翻倍，且单条解析失败不能影响其它条目。

**步骤 1｜先证明需要并发**（走完阶梯的前三级再谈线程）：
- 更快的算法：`payload` 复用已编译的正则对象 → 单独省掉约三成时间；批处理复用解析上下文 → 再省一成。
- 异步：解析是 CPU 密集，事件循环/协程不带来并行收益。
- 结论：算法与批处理已吃掉大部分收益，但剩余解析仍 CPU 密集且能按条目切分 → 上多线程。

**步骤 2｜定并发形态**：用线程池，不用 `std::async`——任务短、数量大，每次新建线程的开销会盖过收益（CP.41）；worker 数取硬件并发数。

**步骤 3｜定共享状态**：输入条目只读，**不需要加锁**；只有聚合结果需要保护。让每个 worker 先在局部累加，收尾时加锁合并一次，而不是每条都加锁（CP.43）。

**步骤 4｜定错误路径**：解析失败的条目要收集成错误记录，**绝不能让异常逃出 worker 线程函数**——逃出去就是 `std::terminate`，整个进程崩（E.1）。

**步骤 5｜实现**：

```cpp
class ThreadPool {
public:
    explicit ThreadPool(std::size_t n) : stop_(false) {
        for (std::size_t i = 0; i < n; ++i)
            workers_.emplace_back([this]{
                for (;;) {
                    std::function<void()> task;
                    {
                        std::unique_lock lock(mtx_);
                        cv_.wait(lock, [this]{ return stop_ || !tasks_.empty(); });
                        if (stop_ && tasks_.empty()) return;
                        task = std::move(tasks_.front());
                        tasks_.pop();
                    }
                    task();
                }
            });
    }

    ~ThreadPool() {
        {
            std::scoped_lock lock(mtx_);
            stop_ = true;
        }
        cv_.notify_all();
        for (auto& w : workers_) if (w.joinable()) w.join();
    }

    template <class F>
    void submit(F&& f) {
        {
            std::scoped_lock lock(mtx_);
            tasks_.emplace(std::forward<F>(f));
        }
        cv_.notify_one();
    }

private:
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex mtx_;
    std::condition_variable cv_;
    bool stop_;
};
```

提交任务时把失败收进局部结果，最后统一合并：

```cpp
ThreadPool pool(std::thread::hardware_concurrency());
std::mutex agg_mtx;
std::map<Level, std::size_t> counts;
std::vector<std::string> errors;

for (const auto& e : entries) {
    pool.submit([&, e]{                       // 按值捕获条目，避免悬垂（CP.31）
        try {
            auto parsed = parse_payload(e.payload);
            std::scoped_lock lock(agg_mtx);   // 合并只在收尾时加锁
            ++counts[parsed.level];
        } catch (const std::exception& ex) {
            errors.push_back(std::string(e.id) + ": " + ex.what());
        }
    });
}
```

**步骤 6｜停机**：析构时 `stop_ = true` → `notify_all()` → `join()` 全部 worker；队列里未处理的任务被丢弃——需要取回失败信息时改用 `std::shared_future`（CP.60）。

**步骤 7｜验证**：
- 条目守恒：成功数 + 失败数 == N。
- TSan 干净：`thread` sanitizer 跑一遍，任务队列与结果合并处不应有报告（CP.9）。
- 无死锁：worker 若可能长时间阻塞，改用 `std::jthread` + `stop_token` 让它能被中断；等待谓词里同时检查停止标志（见上文 `stop_ || !tasks_.empty()`）。

## Key Takeaways

1. 默认单线程；加线程前先走完"更快算法 → 批处理 → 异步"三级阶梯（Per.1、Per.2、CP.4）。
2. 数据竞争的判定是"同一地址 + 并发 + 至少一个写 + 无同步"，命中即未定义行为，不是"读到旧值"（CP.2）。
3. 内存序默认 `memory_order_seq_cst`；只有测量证明锁是瓶颈才降级，弱序用错比用慢可怕得多（CP.101）。
4. 锁一律 RAII，多锁用 `std::scoped_lock`，持锁期间绝不调用未知代码（CP.20、CP.21、CP.22）。
5. 条件变量必须带谓词，状态改变必须持锁，通知放在解锁之后（CP.42）。
6. 临界区里只留数据访问，慢操作取快照后放到锁外（CP.43）。
7. 优先用 `std::mutex`；无锁不是"更快"，自己写之前先证明你能证明（CP.100）。

## Connects To

- **Ch01**: 跨线程共享所有权 —— `shared_ptr`／`weak_ptr` 是线程间共享所有权的默认工具（R.20、CP.32）；小数据优先按值传（CP.31）。
- **Ch06**: 错误在并发下如何传播 —— `future::get()` 会重抛任务里的异常；线程池 worker 里的未捕获异常会直接 `std::terminate`（E.1、CP.60）。
- **Ch10**: TSan 验证 —— 把"没证明没竞争"变成工具可查（CP.9）；线程池与任务队列是最典型的 TSan 目标。
- **Ch11**: 并发类陷阱 —— 悬垂、虚假唤醒、死锁、伪共享都属于同一类"直觉骗人"的陷阱（CP.42、CP.43）。
- **`std::jthread`**：C++20 的自动 join 线程，析构时请求停止并等待结束，是手写 `ThreadGuard` 的标准库版本。
- **`std::promise` / `std::future`**：跨线程回传单值的通道，异常经 `future` 传播，是并发错误处理的入口。
