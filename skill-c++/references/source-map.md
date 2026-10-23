# 来源路由表（生成物，勿手改）

> 由 `build_indexes.py` 生成：路由规则写在脚本里，**路径逐个现场验证**。
> 知识库目录变动后重跑生成器即可，不会出现指向已删除文件的死链。

## 按问题类型查

| 我要查 | 位置 | 说明 |
|---|---|---|
| 某条规则的原文到底怎么说 | `01-core-guidelines/CppCoreGuidelines.md` ✅ | 按规则号 grep；中文全译见 02-core-guidelines-zh/CppCoreGuidelines-zh-CN.md |
| 所有权 / 生命周期 / 智能指针 | `topics/ownership-and-lifetime.md` ✅ | R.11 / R.20 / R.21 / R.24，Rule of Zero/Five |
| 移动语义 / 完美转发 / noexcept | `topics/move-semantics.md` ✅ | std::move / std::forward |
| 模板与 Concepts | `topics/templates-and-concepts.md` ✅ | C++20 concepts 与约束写法 |
| STL 容器 / 算法 / 迭代器失效 | `topics/stl-containers-algorithms.md` ✅ | 含 std::remove 误用、erase-remove 惯用法 |
| 并发 / 数据竞争 / 内存序 | `topics/concurrency.md` ✅ | 对应 Core Guidelines 的 CP.* 规则 |
| 错误处理 / 异常安全 | `topics/error-handling.md` ✅ | E.* 规则与异常安全三保证 |
| 性能优化 | `topics/performance.md` ✅ | Per.* 规则与可测量的优化 |
| C++11/14/17/20/23 特性速查 | `06-modern-cpp-features/` ✅ | 每个版本一个文件，外加 modern-cpp-features-cheatsheet.md |
| 陷阱与反模式 / UB 清单 | `topics/pitfalls-and-antipatterns.md` ✅ | 17 类高频坑 |
| CMake / CI / 测试工程 | `topics/project-practices.md` ✅ | 搭一个可交付的 C++ 工程 |
| CMake 最佳实践（可直接抄的模板） | `13-cmake-best-practices/` ✅ | 含 CMakePresets、工具链、依赖管理 |
| 编译 / 调试 / Sanitizer | `topics/toolchain-and-debugging.md` ✅ | ASan / UBSan / TSan 用法 |
| Google C++ 风格指南 | `09-google-style/cppguide.md` ✅ | HTML 转 Markdown；中文版在 10-google-style-zh/ |
| 标准库 API 语义（权威） | `18-cppreference-doc/headers-md/` ✅ | 按头文件分篇，如 memory.md / vector.md / algorithm.md |
| ISO 标准草案原文 | `12-iso-draft/markdown/` ✅ | 39 篇按标准章节拆分 |
| 算法实现 + 单元测试 | `07-algorithms/` ✅ | 按算法分类的目录树 |
| 算法题解（C++） | `08-leetcode-cases/` ✅ | 0001-1000.md 等分段题解 |
| 中文系统教程 | `19-learncpp-cn/` ✅ | learncpp.com 中文全译 |
| 中文面试知识点 / 短文 | `20-cpp-notes-cn/` ✅ | 智能指针.md 等 11 篇短文 |
| 真实工程示例（实时系统） | `11-real-time-cpp/` ✅ | 书稿 + 配套工程 |
| 现代 C++ 工程脚手架 | `14-modern-cpp-starter/` ✅ | clang-format / CMake 模板 |

## 三层知识结构的分工

| 层 | 目录 | 用途 |
|---|---|---|
| 原文层 | `01-` ~ `20-` | 上游仓库原文，一字不改；含中文主题页 `topics/` 与索引页 `index/` |
| 主题层 | `topics/` | 中文原创消化层，11 篇，结构为「结论 → 规则 → 案例 → 坑 → 出处」 |
| 索引层 | `index/` | 来源台账、学习路线、案例索引、知识地图 |

## 总入口

- 知识地图：`index/knowledge-map.md`
- 来源台账（作者 / 许可 / star / commit）：`index/sources.md`
- 学习路线：`index/learning-path.md`
- 案例索引：`index/cases.md`
