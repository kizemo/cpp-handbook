# 章节生成计划（15 章）

每章的固定规则见 `chapter-template.md`。本文件给出每章的**专属信息**。

| 章 | 标题 | 源文件 | 规则号前缀提示 | 特有要求 |
|---|---|---|---|---|
| ch01 | 所有权与生命周期（Ownership & Lifetime） | `knowlege/topics/ownership-and-lifetime.md` | R.*、E.6、C.21、C.67 | 所有权类型速查表 |
| ch02 | 移动语义与完美转发（Move Semantics & Perfect Forwarding） | `knowlege/topics/move-semantics.md` | F.*、Per.* | 值类别对照表 |
| ch03 | 模板与 Concepts（Templates & Concepts） | `knowlege/topics/templates-and-concepts.md` | T.* | SFINAE vs requires 对比表 |
| ch04 | STL 容器与算法（STL Containers & Algorithms） | `knowlege/topics/stl-containers-algorithms.md` | ES.*、C.* | 容器选型表 + 迭代器失效表 |
| ch05 | 并发编程（Concurrency） | `knowlege/topics/concurrency.md` | **CP.*** | 锁家族对照表 |
| ch06 | 错误处理（Error Handling） | `knowlege/topics/error-handling.md` | E.*、F.* | 三种机制对比表 |
| ch07 | 性能优化（Performance Optimization） | `knowlege/topics/performance.md` | Per.* | 优化优先级表 |
| ch08 | 现代 C++ 特性全景（Modern C++ Features） | `knowlege/topics/modern-cpp-features.md` | 各类 | 按版本特性表 + 选型决策表 |
| ch09 | 工程实践（Project Practices） | `knowlege/topics/project-practices.md` | 各段自有 | 目录结构 + CI 流水线 |
| ch10 | 工具链与调试（Toolchain & Debugging） | `knowlege/topics/toolchain-and-debugging.md` | 各段自有 | 工具对照表（工具→查什么） |
| ch11 | 陷阱与反模式（Pitfalls & Antipatterns） | `knowlege/topics/pitfalls-and-antipatterns.md` | ES.*、R.*、C.* | 坑位清单（含工具检出手段） |
| ch12 | 案例索引（Cases） | `knowlege/index/cases.md` | — | 案例来源与使用纪律 |
| ch13 | 学习路线（Learning Path） | `knowlege/index/learning-path.md` | — | 四阶段路线表 |
| ch14 | 来源台账（Sources） | `knowlege/index/sources.md` | — | 20 个来源的选源指南 |
| ch15 | 知识地图与库结构（Knowledge Map & Repository Layout） | `knowlege/index/knowledge-map.md` + `knowlege/README.md` | — | 三层结构图 + 双链约定 |

## Connects To 指引（每章至少 4 条）

- ch01 → ch02, ch06, ch04, ch05, ch11
- ch02 → ch01, ch11, ch08, ch04
- ch03 → ch08, ch04, ch11, ch01
- ch04 → ch11, ch03, ch01, ch07
- ch05 → ch01, ch06, ch10, ch11
- ch06 → ch01, ch02, ch10, ch05
- ch07 → ch05, ch11, ch10, ch04
- ch08 → ch02, ch03, ch04, ch06
- ch09 → ch10, ch11, ch14, ch15
- ch10 → ch09, ch11, ch05, ch07
- ch11 → ch01, ch02, ch04, ch05, ch06, ch08, ch09, ch10, ch07
- ch12 → ch15, ch13, ch01–ch11
- ch13 → ch12, ch15, ch08
- ch14 → ch15, ch09
- ch15 → ch12, ch13, ch14, ch01–ch11

## 引用规则号的三条硬规矩

1. 写任何规则号之前，先在 `knowlege/_meta/core-guidelines-rules.txt` 里搜到它（500 条）。
2. 搜不到就不写。**写错比不写更糟**——错编号会让整段论证失效。
3. 前缀含义：并发 `CP.` / 性能 `Per.` / 所有权资源 `R.` / 宏语句 `ES.` /
   类 `C.` / 函数 `F.` / 错误处理 `E.` / 模板 `T.`。
   `Con.*` 是 const/不可变默认的旧章节（只有 5 条），**不要**用它表示并发。

## 自验命令

```powershell
python F:\soft\00selfmade\skill-c++\skill-c++\scripts\rule_lint.py F:\soft\00selfmade\skill-c++\skill-c++\chapters\<你的文件名>
```

必须 **0 错误**。有 ERROR 就修到没有为止（WARN 可以接受，但要看一眼是不是真问题）。
