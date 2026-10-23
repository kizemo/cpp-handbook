# Chapter 9: 工程实践（Project Practices）

## Core Idea

现代 C++ 工程的标配是 **CMake + 单元测试 + 静态分析 + Sanitizer + CI**，目标只有一个：**让 bug 在提交前暴露，而不是在生产环境暴露**。工具不是加分项——P.12 要求按需使用配套工具，CP.9 要求用工具验证并发代码；没有工具链的"规范"只是口头约定。

## Frameworks Introduced

- **Target-based CMake（目标导向构建）**：把编译选项、include 路径、依赖全部挂在 target 上，用 `PUBLIC`/`PRIVATE`/`INTERFACE` 决定传播范围。
  - When to use: 任何做成库的 target，尤其是要被别的项目 `find_package` 消费时。
  - How: `add_library` + `target_include_directories` + `target_compile_features`；对外只暴露 `MyLib::mylib` 一个稳定名字；构建与安装路径用 `$<BUILD_INTERFACE:>` / `$<INSTALL_INTERFACE:>` 分流。
- **警告即错误（Warnings as Errors）**：把编译器警告升级为构建失败。
  - When to use: 自有代码的全部 target。
  - How: `-Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wsign-conversion` 加 `-Werror`（MSVC 用 `/W4 /permissive- /WX`）。`-Wconversion` 对应 ES.46（避免有损的窄化算术转换），`-Wsign-conversion` 对应 ES.100（别混用有符号与无符号算术）；第三方 target 不 link 这组选项。
- **测试金字塔（Test Pyramid）**：大量快速单元测试 + 少量集成测试 + 极少量 E2E。
  - When to use: 每个 PR 都跑。
  - How: 一个测试只测一件事；`ASSERT_*` 提前退出、`EXPECT_*` 继续检查；测公开行为不测实现细节；每个 bug 修复补一条回归测试。
- **Sanitizer 组合**：用运行时插桩把未定义行为（undefined behavior）变成确定性报告。
  - When to use: 本地日常开 ASan+UBSan；CI 必跑；并发代码额外跑 TSan（CP.9）。
  - How: `-fsanitize=address,undefined -fno-omit-frame-pointer -g`；MSVC 用 `/fsanitize=address /Zi`。
- **可复现构建（CMakePresets）**：把构建配置写成入库的预设文件。
  - When to use: 多配置、多人协作、需要本地与 CI 一致时。
  - How: `configurePresets` 定义 `dev`/`release`，`inherits` 派生；配套 `buildPresets`、`testPresets`；一条龙 `cmake --preset dev && cmake --build --preset dev && ctest --preset dev`。
- **依赖锁定（Pinned Dependency）**：所有第三方依赖固定到具体版本。
  - When to use: 每一个第三方依赖。
  - How: `FetchContent`/`CPM.cmake` 锁 `GIT_TAG` 到 tag（绝不写 `main`）；包管理器锁版本文件；版本号进版本控制，升级是显式提交而不是意外。

## Key Concepts

- **公共头与实现分离**：`include/` 对外、`src/` 内部，头文件只声明不定义（SF.2）。
- **自包含头文件（self-contained header）**：每个头文件单独编译也能通过——它自己 include 了它需要的一切（SF.11）；这是"删掉一个 include 就崩"的根治办法。
- **include 守卫（include guard）**：每个头文件都要有防重入守卫（SF.8）；`#pragma once` 也可以，但别在同一项目里混用两种风格。
- **可移植头标识符（portable header identifier）**：相对路径用引号形式、系统路径用尖括号形式（SF.12、SF.13）。
- **源文件自证接口**：`.cpp` 先 include 定义其接口的头文件（SF.5），接口不一致在编译期就暴露，而不是等调用方炸。
- **Sanitizer（运行时缺陷检测器）**：插桩运行的编译器/运行时，把越界、UAF、有符号溢出从"偶尔错"变成"每次报"（P.7）；并发代码的数据竞争交给 TSan（CP.9）。
- **行为测试 vs 实现测试**：行为测试断言公开契约，重构不破；实现测试断言内部结构，一重构就红。

## Mental Models

- 把 CMake target 当"带契约的模块"：属性跟着 target 走、跟着依赖关系走，不跟着全局变量走。全局变量是隐式契约，target 属性是显式契约。
- 把 CI 当"裁判"而不是"通知器"：本地绿灯不等于合格，必须多编译器 × 多标准 × Sanitizer 一起过才算数。
- 把 Sanitizer 当"运行时断言工厂"：它把编译器管不着、测试又碰不到的那一类错误变成可复现的失败。

## Anti-patterns

- **全局 CMake 变量污染**：`set(CMAKE_CXX_FLAGS "-Wall -Werror")` 会渗进所有子目录与第三方依赖，外部代码的警告也会让构建失败。
- **相对路径 include**：`#include "../../src/foo.h"` 让头文件路径依赖目录布局，目录一改就断（SF.12、SF.13）。
- **头文件里放定义或 `using namespace`**：非 inline 函数定义或对象定义放进头文件 → 多重定义链接错误（SF.2）；全局 `using namespace` 会把命名空间污染泄给所有包含者（SF.7）。
- **给第三方代码开 `-Werror`**：别人的警告阻塞自己的构建，一升级依赖就红。
- **只测实现细节**：重构即崩，测试从护栏变成负担。
- **浮动依赖版本**：`GIT_TAG main` —— "昨天还能编过今天挂了"的根源。
- **CI 只跑一种配置**：单编译器、单标准、无 Sanitizer、无格式检查，等于没有 CI。
- **格式化配置不入库**：每次 review 都在吵格式，注意力被格式吃光。

## Code Examples

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyLib VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)          # 不用 GNU 扩展，保持可移植

add_library(mylib
    src/parser.cpp
    src/detail/helper.cpp
)
add_library(MyLib::mylib ALIAS mylib)   # 别名，方便外部使用

target_include_directories(mylib
    PUBLIC  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:include>
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_compile_features(mylib PUBLIC cxx_std_20)
```

- **What it demonstrates**: target-based 写法——属性跟着 target 走，`PUBLIC` 的 include 路径随依赖传播，`PRIVATE` 的不传播。

```cmake
# cmake/CompilerWarnings.cmake
add_library(project_warnings INTERFACE)
target_compile_options(project_warnings INTERFACE
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /permissive- /WX>
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic
                                 -Wshadow -Wconversion -Wsign-conversion -Werror>
)
```

- **What it demonstrates**: 警告选项做成 `INTERFACE` target 复用——只让自有 target link 它，第三方 target 不受影响。

```cpp
// ✗ 相对路径：目录一改就断，还把私有 src 泄漏给外部使用者
#include "../../src/detail/helper.h"

// ✓ 公共接口：引号 + 稳定路径，外部只需看见 include/mylib
#include "mylib/parser.h"
```

- **What it demonstrates**: 引号形式与尖括号形式的分工（SF.12、SF.13）；公共头对外，内部头不对外。

```cpp
#include <gtest/gtest.h>
#include "mylib/parser.h"

TEST(ParserTest, ParsesSimpleExpression) {
    mylib::Parser p;
    auto result = p.parse("1 + 2");
    ASSERT_TRUE(result.has_value());   // 前提不成立就退出
    EXPECT_EQ(*result, 3);             // 前提成立后继续检查其余断言
}

TEST(ParserTest, RejectsMalformedInput) {
    mylib::Parser p;
    EXPECT_FALSE(p.parse("1 +").has_value());
}
```

- **What it demonstrates**: 一个测试只测一件事；`ASSERT_*` 与 `EXPECT_*` 的分工。

## Reference Tables

### 工程目录布局

| 目录 | 放什么 | 关键约束 |
|---|---|---|
| `CMakeLists.txt`（顶层） | 项目声明、target 定义、`enable_testing()` | 只做编排，不写编译选项 |
| `cmake/` | `CompilerWarnings.cmake`、`Sanitizers.cmake` 等可复用模块 | 用 `include()` 引入 |
| `include/mylib/` | 公共头文件，对外唯一入口 | 自包含（SF.11）、不写定义（SF.2） |
| `src/` | 实现文件与内部头 | 内部头不安装、不导出 |
| `tests/` | 单元测试，独立 `CMakeLists.txt` | 顶层 `enable_testing()` + `add_subdirectory(tests)` |
| `CMakePresets.json` | 构建预设 | 与 CI 共用同一份配置 |
| `.clang-format` / `.clang-tidy` | 格式化与静态分析配置 | 入库，并由 CI 校验 |

### Sanitizer 对照

| Sanitizer | 查什么 | 典型报告 |
|---|---|---|
| **ASan**（AddressSanitizer） | 越界、use-after-free（UAF） | "heap-use-after-free" |
| **UBSan**（UndefinedBehaviorSanitizer） | 有符号溢出、非法移位、错误对齐 | "signed integer overflow" |
| **TSan**（ThreadSanitizer） | 数据竞争、死锁（CP.9） | "data race" |
| **MSan**（MemorySanitizer） | 未初始化内存读取 | "use-of-uninitialized-value" |
| **ASan+UBSan** 组合 | 覆盖面最广 | — |

### 静态分析与格式化工具

| 工具 | 作用 | 何时进 CI |
|---|---|---|
| **clang-tidy** | 静态分析 + 自动修复（几百个 check） | 必跑，可先只报不失败 |
| **clang-format** | 代码格式化（Google / LLVM / 自定义风格） | 必跑，用 `--dry-run --Werror` 查差异 |
| **cppcheck** | 轻量静态分析，不依赖编译器 | 可选，适合没有 clang 的环境 |
| **PCLint / PVS-Studio** | 商业深度分析 | 按需 |

`modernize-*` 这组检查拦的正是"手写旧式替代品"，与 ES.1（优先标准库而不是手搓代码）同向。

### 依赖管理方式

| 方式 | 适用 | 注意 |
|---|---|---|
| **CMake `FetchContent`** | 少量源码依赖，直接嵌入构建 | 锁 `GIT_TAG` |
| **CPM.cmake** | FetchContent 的增强版，脚本化 | 同样锁版本 |
| **vcpkg** | 跨平台包管理，Windows 生态好 | 锁 manifest |
| **Conan 2** | 跨平台包管理，Linux 生态好 | 锁 lockfile |
| **git submodule** | 传统但仍然可靠 | 记得提交 submodule 指针 |

## Worked Example

**场景**：把一个只有两个 `.cpp` 的小库 `mylib` 升级成可交付的工程——多编译器可编、有单测、有 Sanitizer、CI 绿灯、依赖可复现。

**步骤 1｜搭骨架**（目录布局见上表；头文件自包含是硬要求）

`include/mylib/parser.h` 顶部放 include 守卫（SF.8），并且只 include 自己真正用到的标准头（SF.10、SF.11）。`src/parser.cpp` 第一行 include `"mylib/parser.h"`（SF.5）——头里漏掉某个类型声明时，这里立刻编译失败，而不是等到使用者才炸。

**步骤 2｜target-based 顶层 CMakeLists**（在上面的 target 示例基础上补齐工程接线）

```cmake
include(cmake/CompilerWarnings.cmake)
include(cmake/Sanitizers.cmake)

add_library(mylib src/parser.cpp src/detail/helper.cpp)
add_library(MyLib::mylib ALIAS mylib)
target_link_libraries(mylib PRIVATE project_warnings)   # 只自有 target 吃 -Werror

enable_testing()
add_subdirectory(tests)
```

关键点：`project_warnings` 只 link 到 `mylib`；`FetchContent` 拉进来的第三方 target 不会继承它，第三方代码的警告因此不会阻塞你的构建。

**步骤 3｜测试与依赖**

```cmake
# tests/CMakeLists.txt
include(FetchContent)
FetchContent_Declare(googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.15.2          # 锁定版本，不要用 main
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(googletest)

add_executable(parser_test parser_test.cpp)
target_link_libraries(parser_test PRIVATE MyLib::mylib GTest::gtest_main)
gtest_discover_tests(parser_test)
```

`GTest::gtest_main` 是 googletest 自带的别名 target，用它而不是手写 `include_directories()`。

**步骤 4｜Sanitizer**

```cmake
# cmake/Sanitizers.cmake
option(MYLIB_ENABLE_SANITIZER "Enable ASan+UBSan" OFF)
if(MYLIB_ENABLE_SANITIZER AND NOT MSVC)
    target_compile_options(mylib PUBLIC -fsanitize=address,undefined
                                              -fno-omit-frame-pointer -g)
    target_link_options(mylib PUBLIC -fsanitize=address,undefined)
endif()
```

本地与 CI 用同一条命令：`cmake --preset dev -DMYLIB_ENABLE_SANITIZER=ON`。

**步骤 5｜CI 流水线**

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        std: [20, 23]
        compiler: [gcc, clang]
    steps:
      - uses: actions/checkout@v4
      - name: Configure
        run: cmake --preset dev -DCMAKE_CXX_STANDARD=${{ matrix.std }}
      - name: Build
        run: cmake --build --preset dev
      - name: Test
        run: ctest --preset dev
      - name: Sanitizers
        run: |
          cmake --preset dev -DMYLIB_ENABLE_SANITIZER=ON
          cmake --build --preset dev && ctest --preset dev
```

再加两个 job：`format`（`clang-format --dry-run --Werror .`）与 `tidy`（`clang-tidy` 或 `run-clang-tidy`）。若库里有并发代码，再单独加一个 TSan job——这是唯一能客观证明"没有数据竞争"的手段（CP.9）。

**步骤 6｜验收标准**（逐条可勾选）

- `cmake --preset dev && cmake --build --preset dev && ctest --preset dev` 全绿，且整套单测几秒内跑完。
- 同一个 commit 在 gcc 与 clang、C++20 与 C++23 下都通过。
- ASan+UBSan 构建下跑完整套件无报告；并发部分有 TSan job 覆盖。
- `clang-format --dry-run --Werror .` 无输出；依赖版本写死在 `GIT_TAG` 或 manifest 里。

## Key Takeaways

1. 用 target 属性取代全局变量；对外只暴露 `MyLib::mylib` 一个稳定名字，依赖随 target 自动传播。
2. 公共头必须自包含（SF.11）、只声明不定义（SF.2）、带 include 守卫（SF.8）；`.cpp` 先 include 自己的头（SF.5）；相对路径用引号、系统路径用尖括号（SF.12、SF.13）。
3. 自有代码一律 `-Werror`；`-Wconversion` 与 `-Wsign-conversion` 对应 ES.46 与 ES.100；第三方 target 不吃这组选项。
4. CI 至少覆盖：多编译器 × 多标准、单元测试、ASan+UBSan、并发代码的 TSan（CP.9）、静态分析、格式检查。
5. 依赖锁到 tag；`main`/`master` 是随机失败的根源，升级依赖必须是显式提交。
6. 测试只测公开行为；bug 修复带回归测试；套件要快到开发者愿意每次都跑。
7. 格式化配置入库并由 CI 校验——消灭格式争论，把 review 留给设计。

## Connects To

- **Ch10**: 工具链与调试 —— Sanitizer 报告怎么读、栈怎么回溯、调试器怎么配，本章只规定"必须跑"，那一章讲"怎么用"。
- **Ch11**: 陷阱与反模式 —— 工程实践挡不住的语义坑（宏、隐式转换、全局状态）需要靠静态分析与阅读规则来补。
- **Ch14**: 来源台账 —— CMake 最佳实践模板、ModernCppStarter、维护性指南的出处与选源依据。
- **Ch15**: 知识地图与库结构 —— 本知识库自身的目录分层与双链约定，就是本章工程实践的一个实例。
- **Ch07**: 性能优化 —— 把 benchmark 与 PGO 纳入 CI，用测量替代直觉（Per.6、Per.7）。

### EXTRACT ch09
TERMS: 目标导向构建（target-based CMake） | 警告即错误（warnings as errors） | 自包含头文件（self-contained header） | 运行时缺陷检测器（Sanitizer） | 测试金字塔（test pyramid） | 可复现构建（reproducible build） | 依赖锁定（pinned dependency）
PATTERNS: 头文件/实现分离且自包含（何时用：库对外暴露接口时；做法：公共头只声明、带 include 守卫并自包含，.cpp 先 include 自己的头） | target-based CMake 加 INTERFACE 警告 target（何时用：任何做成库的 target；做法：属性挂 target，用 PUBLIC/PRIVATE/INTERFACE 传播，只让自有 target link -Werror） | Sanitizer 进 CI（何时用：每次提交的 CI；做法：常规跑 ASan+UBSan，并发代码额外跑 TSan，按报告栈定位）
DECISIONS: 当公共头要跨项目复用时让它自包含并只声明不定义，因为只有自包含才能被任意调用方直接包含（SF.11、SF.2） | 当编译器警告出现在第三方代码里时降级为不失败，而不是全局 -Werror，因为别人的警告不该阻塞自己的构建 | 当依赖需要升级时锁到具体 tag 而不是 main，因为浮动版本会让 CI 随机失败
TABLE: 缺陷检测手段对照（行：编译器警告 / Sanitizer / clang-tidy / 单元测试 / CI 多配置矩阵；列：各自能抓到的缺陷类别）
