# 术语表

> 按英文术语排序，附中文释义与出处章节。

**address sanitizer (ASan)** — 运行时内存检查器，检出越界、释放后使用、泄漏（Ch10, Ch09）
**algorithm (STL 算法)** — 标准库提供的通用操作，优先于手写循环（Ch04）
**aliasing** — 通过另一个对象的地址访问对象；类型双关可能违反严格别名规则（Ch11）
**ampersand-pile (&&-pile)** — 右值引用；表达"我要接管这个对象"（Ch02）
**concepts (C++20)** — 编译期模板参数约束机制，取代 SFINAE（Ch03, Ch08）
**copy elision (拷贝消除)** — 编译器省略拷贝/移动构造，C++17 起部分场景强制保证（Ch02）
**CRTP** — 奇异递归模板模式，用基类模板参数实现静态多态（Ch03）
**data race (数据竞争)** — 两个线程访问同一内存、至少一个是写、且无同步（Ch05）
**deadlock (死锁)** — 多个锁互相等待；用 `std::scoped_lock` 一次获取可避免（Ch05）
**delegating constructor (委托构造)** — 构造函数委托给同一类的另一个构造函数（C.51）（Ch01）
**deleter (删除器)** — 智能指针的清理策略；`FILE*` 需要 `fclose` 而非 `delete`（Ch01）
**deterministic (可确定性)** — 同样输入必得同样输出，无 UB 隐藏（Ch10）
**exception safety (异常安全)** — 抛异常后对象仍处于有效状态；分基本/强/不抛三级（Ch06）
**explicit constructor** — 禁止隐式转换的构造函数，防止意外类型转换（Ch01）
**final_action** — 无合适资源句柄时的兜底清理 guard（E.19）（Ch06）
**forwarding reference (转发引用)** — `T&&` 且 T 是本函数模板参数时，保留值类别（Ch02）
**hard error (硬错误)** — 会导致未定义行为的缺陷；工具优先检出（Ch11）
**iterator invalidation (迭代器失效)** — 容器操作使已有迭代器/引用不再有效（Ch04, Ch11）
**lvalue / rvalue** — 左值有身份可寻址，右值是临时值；C++11 起按值类别三分（prvalue/xvalue/lvalue）（Ch02）
**memory order (内存序)** — 原子操作与其它内存操作之间的顺序约束强度（Ch05）
**move semantics (移动语义)** — 把资源所有权转移出去，避免深拷贝（Ch02, Ch01）
**mutable** — 允许在 `const` 成员函数里修改的成员（Ch11）
**noexcept** — 异常规格；标注移动操作才能让 `vector` 扩容走真移动（Ch02, Ch06）
**object lifetime (对象生命周期)** — 对象从构造完成到析构开始之间的区间（Ch01）
**ownership (所有权)** — 谁负责释放某个资源（Ch01）
**perfect forwarding (完美转发)** — 把实参的值类别原封不动传到下一层（Ch02）
**pointer-to-member** — 成员函数/成员指针；不参与重载决议，容易误用（Ch11）
**RAII** — Resource Acquisition Is Initialization，构造获取、析构释放（Ch01, Ch06）
**Rule of Zero / Five** — 零特殊成员函数 vs 五个全套（Ch01）
**sanitizer** — 编译期插入插桩的运行时检查器：ASan/UBSan/TSan（Ch10）
**SFINAE** — C++17 之前的模板约束机制，错误信息难读（Ch03）
**shared_ptr** — 共享所有权；环形引用会导致计数永不归零（Ch01）
**sign bit** — 浮点数的符号位；符号 NaN 参与比较会引发未定义行为（Ch07）
**span (C++20)** — 非拥有的连续序列视图，替代 `ptr + len`（Ch04）
**static initialization order fiasco** — 跨翻译单元的全局对象初始化顺序未定义（Ch11）
**string_view** — 非拥有的字符串视图，悬垂风险高（Ch04, Ch11）
**strong exception guarantee** — 抛异常后状态与调用前完全一致（Ch06）
**type erasure** — 运行期多态、编译期接口的类型擦除手法（Ch03）
**UB (未定义行为)** — 标准不规定后果的行为；编译器可任意生成代码（Ch11, Ch10）
**unique_ptr** — 唯一所有权，不可拷贝可移动（Ch01）
**value category (值类别)** — 决定表达式能否被移动/拷贝的分类（Ch02）
**weak_ptr** — 观察者，不延长生命周期，用于破环与缓存（Ch01）
**wobbly rule** — "悬垂的 `string_view`" 等寿命问题的通用形态（Ch04）
**zero-cost abstraction** — 抽象不引入运行时开销（Ch03, Ch07）
