# Chapter 10: 工具链与调试（Toolchain & Debugging）

## Core Idea

UB 不是"没崩就没事"，它是沉默的数据损坏。定位靠 **Sanitizer + 调试器 + 核心转储**，不是加 `printf`。

## Frameworks Introduced

- **双构建矩阵（Release + Debug/Sanitizer）**
  - When to use: 第一天就进 CI。
  - How: Release `-O2 -g -Wall -Wextra -Wpedantic`，Debug `-Og -g3` 加 sanitizer；两套都要有。编译器：GCC 标准、Clang 诊断好、MSVC 配 VS、oneAPI 偏 SIMD。
- **Sanitizer 家族（ASan / UBSan / TSan / MSan）**
  - When to use: 内存错误、UB、竞争、未初始化；也作 CI 门禁。
  - How: 编译期插桩，把 UB 变成明确诊断，不是随机崩溃或静默错误。
- **崩溃现场取证（调试器 + 核心转储）**
  - When to use: 已知位置要看控制流，或崩溃发生在无值守环境。
  - How: 断点 → `bt` → `frame N` → `watch` 追写入者；崩溃前 `ulimit -c unlimited`，崩溃后 `gdb ./app <core>` + `bt full`。
- **性能剖析（perf / callgrind / VTune / Instruments）**
  - When to use: 想知道时间花在哪个函数。
  - How: perf 采样找热点，callgrind 精确计数；先测量再下结论。
- **外部验证层（Valgrind + 模糊测试）**
  - When to use: 不想重编译；或给解析器生成畸形输入。
  - How: Valgrind 不重编译查泄漏；fuzz 入口 + 语料库喂畸形输入。

## Key Concepts

- **未定义行为（undefined behavior, UB）**：标准未规定语义；编译器可任意生成代码，最坏结果离现场很远。
- **插桩（instrumentation）**：编译期插入检查代码，sanitizer 与精确计数型 profiler 靠它。
- **核心转储（core dump）**：崩溃瞬间的内存镜像，含栈、寄存器与各线程状态。
- **硬件观察点（watchpoint）**：借 CPU 硬件寄存器实现"变量一变就停"，用来找写入者。
- **数据竞争（data race）**：两线程并发访问同一内存、至少一个为写且无同步。

## Mental Models

- 把 UB 当"沉默的破坏者"：它不报错，只把内存搞坏，几天后在无关处爆炸——所以 UBSan 要 `-fno-sanitize-recover=all`，一发现就停。
- 把工具当"分工的目击者"：Sanitizer 看内存与 UB，调试器看控制流，core dump 看崩溃瞬间，profiler 看时间去向。
- 把"崩溃"当"可复现输入"：不能稳定复现时先缩小输入、记录种子、加日志，别急着上工具。

## Anti-patterns

- **用 `printf` 代替调试器**：看不到栈帧与变量，最后一条日志往往不是出错点。
- **只构建 Release**：`-O2` 下变量可能被优化掉，UB 被掩盖。
- **UBSan 不加 `-fno-sanitize-recover=all`**：检出 UB 后继续跑，输出垃圾结果。
- **ASan 与 TSan 同时启用**：内存布局不同，结论互相污染——分两次构建（CP.9）。
- **靠猜做性能优化**：没测量就改代码，越改越慢（Per.1、Per.6）。

## Code Examples

```bash
# Release：带符号、警告全开、保留帧指针
g++ -std=c++20 -O2 -g -Wall -Wextra -Wpedantic -fno-omit-frame-pointer -o app main.cpp
# Debug：ASan + UBSan（遇 UB 立即中止）
g++ -std=c++20 -Og -g3 -fsanitize=address,undefined -fno-sanitize-recover=all -o app-asan main.cpp
# 竞态专用：与 ASan 互斥，单独构建
g++ -std=c++20 -O1 -g -fsanitize=thread -o app-tsan main.cpp
```

- **What it demonstrates**: 三种构建——Release 带符号、ASan+UBSan 抓内存与 UB、TSan 抓竞争。

```gdb
break parser.cpp:42           # 按行设断点
run arg1 arg2                 # 运行
bt                            # 打印调用栈（backtrace）
watch counter                 # 硬件 watchpoint：变量一变就停
```

- **What it demonstrates**: 调试器常用动作——断点定位、看栈、追写入者。

## Reference Tables

### 工具 → 查什么

| 工具 | 查什么 | 代价 / 限制 |
|---|---|---|
| **ASan** | 堆/栈越界、use-after-free、double-free、泄漏 | 需重编译；与 TSan 互斥 |
| **UBSan** | 整数溢出、非法移位、空指针解引用、越界下标 | 须加 `-fno-sanitize-recover=all` |
| **TSan** | 数据竞争 | 与 ASan 不能同时启用，分两次构建 |
| **MSan** | 未初始化内存的读取 | 所有依赖库都要 MSan 编译 |
| **GDB / LLDB** | 控制流、断点、变量、栈帧 | 依赖调试信息；`-O2` 下丢变量 |
| **core dump** | 崩溃瞬间的内存快照与线程状态 | 崩溃前须设 `ulimit -c unlimited` |
| **perf / callgrind** | 热点采样统计 / 精确指令计数 | 需保留符号 / 慢但准 |
| **Valgrind memcheck** | 泄漏与非法读写 | 不需重编译；慢 10–50 倍 |
| **libFuzzer / AFL++** | 畸形输入触发的解析崩溃 | 需要 fuzz 入口 |

### 崩溃诊断清单（先做下一步，再看结果）

1. 能稳定复现吗？不能 → 缩小输入、记录种子、加日志。
2. 用 Sanitizer 重编译再跑：ASan 查内存、UBSan 查 UB、TSan 查竞争。
3. 还是崩 → 生成 core dump，`bt full` 看栈。
4. 段错误但没崩 → 查空指针、越界、栈溢出、栈破坏（ASan）。
5. 结果不对但不崩 → 查未初始化、整数溢出、别名规则、有符号/无符号混用（UBSan、MSan）。
6. 怀疑并发 → TSan 单独构建，缩到最小复现（CP.9）。

## Worked Example

**场景**：解析服务偶发 SIGSEGV；另有一批输入"不崩但结果错乱"。两个症状可能同源。

**步骤 1｜先分诊**：崩溃 → 内存路径；结果错 → UB 路径。两者都先固定输入：把线上请求体存成文件当种子——能复现才谈得上定位。

**步骤 2｜ASan 构建跑一遍**（`cmake -B build-asan -DMYLIB_ENABLE_SANITIZER=ON -DCMAKE_BUILD_TYPE=Debug` + `ctest --test-dir build-asan --output-on-failure`），输出直接点名根因 `AddressSanitizer: heap-use-after-free ... in Widget::render() widget.cpp:42`。

**步骤 3｜修根因**（悬垂指针来自手工 `new`/`delete`，R.11、E.6）：

```cpp
// ✗ 悬垂：raw 指针在对象销毁后仍被使用
Widget* w = new Widget();
render(w);
delete w;
use(w);                    // ← heap-use-after-free

// ✓ 值语义或智能指针：生命周期随作用域结束
auto w = std::make_unique<Widget>();
render(*w);
use(*w);
```

**步骤 4｜"不崩但结果错"与并发嫌疑**：换 UBSan 构建并加 `-fno-sanitize-recover=all`，它会指出有符号溢出与混用（ES.100）并在出错那行停住；若栈帧在并发路径，再单独构建 TSan 跑同一批种子（与 ASan 互斥），确认是否还有竞争（CP.2、CP.9）。

**步骤 5｜仍崩且 sanitizer 没报**：崩溃前设 `ulimit -c unlimited`，复现后 `gdb ./app <core>`，`bt full` 看完整栈，`thread apply all bt` 看所有线程。

**步骤 6｜固化门禁**：ASan+UBSan 与 TSan 各一份构建进 CI，`ctest --output-on-failure` 失败即阻断合并（CP.9）；性能问题走 `perf record -g ./app` + `perf report` 定位热点再动手（Per.6）。

## Key Takeaways

1. "没崩"不等于"没 bug"：UB 是沉默的破坏，Sanitizer 才是它的报警器。
2. UBSan 必须配 `-fno-sanitize-recover=all`；ASan 与 TSan 互斥分两次构建；MSan 要求全项目同编。
3. 核心转储要在崩溃前设 `ulimit -c unlimited`；诊断顺序固定：复现 → Sanitizer → core dump → 专项工具，性能先测量再优化（Per.1、Per.6）。

## Connects To

- **Ch09**: 工程实践 —— Sanitizer 与静态分析是构建流水线的常驻门禁，不是临时脚本。
- **Ch11**: 陷阱与反模式 —— 每类 UB 的形态对应本章一个工具（ASan/UBSan/TSan/MSan）。
- **Ch05**: 并发编程 —— TSan 验证并发代码，CP.2 的"避免数据竞争"靠它落地（CP.9）。
- **Ch07**: 性能优化 —— profiler 与基准测试工具；没有测量就没有结论（Per.6）。

### EXTRACT ch10
TERMS: 未定义行为（undefined behavior, UB） | 插桩（instrumentation） | 核心转储（core dump） | 硬件观察点（watchpoint） | 数据竞争（data race）
PATTERNS: 双构建（Release `-O2 -g` + Debug `-Og -g3` 带 sanitizer 进 CI；因为 UB 不崩不报错） | Sanitizer 分工（ASan 查内存、UBSan 查 UB、TSan 查竞争、MSan 查未初始化；一次只开一类） | 崩溃分诊（固定输入使其可复现 → Sanitizer 重编译跑 → 还崩就 core dump + `bt full`）
DECISIONS: 结果不对但不崩时选 UBSan/MSan 而非调试器（这类 UB 不改控制流） | 定位热点时选 perf 采样而非手写计时（手写计时会改变被测代码） | 无值守崩溃选 core dump 而非日志（日志只给得出崩溃前最后一行）
TABLE: 工具 → 查什么（行 = ASan/UBSan/TSan/MSan/GDB/core dump/perf+callgrind/Valgrind/libFuzzer；列 = 查什么 / 代价与限制）
