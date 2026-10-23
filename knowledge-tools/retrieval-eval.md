# 检索评测结果

source: `cpp-knowledge`（embedding 关闭 → 纯 FTS 关键词匹配）

| 提问 | 类型 | 期望页面 | 排名 | top1 命中 |
|---|---|---|---|---|
| 所有权 | 宽泛 | `topics/ownership-and-lifetime` | 2 | `02-core-guidelines-zh/cppcoreguidelines-zh-cn` |
| RAII 资源管理 | 宽泛 | `topics/ownership-and-lifetime` | 3 | `02-core-guidelines-zh/cppcoreguidelines-zh-cn` |
| 移动语义 | 宽泛 | `topics/move-semantics` | 3 | `19-learncpp-cn/content/词汇表/move-semantics` |
| 完美转发 | 精确 | `topics/move-semantics` | 1 | `topics/move-semantics` |
| std::forward | 精确 | `topics/move-semantics` | 1 | `topics/move-semantics` |
| noexcept 移动构造 | 精确 | `topics/move-semantics` | 2 | `02-core-guidelines-zh/cppcoreguidelines-zh-cn` |
| 迭代器失效 | 精确 | `topics/stl-containers-algorithms` | 2 | `20-cpp-notes-cn/迭代器什么时候失效` |
| erase remove | 精确 | `topics/stl-containers-algorithms` | 2 | `08-leetcode-cases-c-remove-invalid-parentheses-cpp` |
|  Concepts 约束 | 精确 | `topics/templates-and-concepts` | 1 | `topics/templates-and-concepts` |
| 悬垂引用 | 精确 | `topics/pitfalls-and-antipatterns` | 4 | `19-learncpp-cn/content/12-复合类型-引用和指针/12-12-return-by-reference-and-return-by-address` |
| shared_ptr 循环引用 | 精确 | `topics/pitfalls-and-antipatterns` | 未召回 | `19-learncpp-cn/content/22-移动语义和智能指针/22-6-std-shared-ptr` |
| data race | 精确 | `topics/concurrency` | 未召回 | `01-core-guidelines/cppcoreguidelines` |
| 内存序 memory_order | 精确 | `topics/concurrency` | 1 | `topics/concurrency` |
| ASan 内存错误 | 精确 | `topics/toolchain-and-debugging` | 1 | `topics/toolchain-and-debugging` |
| 基准测试 benchmark | 精确 | `topics/performance` | 2 | `topics/project-practices` |
| CMake 最佳实践 | 精确 | `topics/project-practices` | 1 | `topics/project-practices` |
| std::expected | 精确 | `topics/error-handling` | 未召回 | `07-algorithms-ciphers-a1z26_cipher-cpp` |
| C++23 新特性 | 精确 | `topics/modern-cpp-features` | 未召回 | `04-modern-cpp-tutorial/book/zh-cn/toc` |
