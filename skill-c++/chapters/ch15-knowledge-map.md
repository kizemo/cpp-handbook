# Chapter 15: 知识地图与库结构（Knowledge Map & Repository Layout）

## Core Idea
知识库分三层：**原文层是证据，主题层是索引，索引层是入口**。
层与层之间只放指针，不复制内容——这样任何一层更新，其余层不会变成第二份真相。

## Frameworks Introduced
- **三层职责分离（Evidence / Index / Entry）**：
  **When to use**：组织任何会持续更新的知识库时。
  **How**：原文层一字不改地存上游；主题层用中文写"结论 → 规则 → 案例 → 坑 → 出处"；
  索引层只做导航，不含知识正文。
- **双链互反（Reciprocal links）**：每个主题页末尾列出它的出边，
  对应页的"相关页面"里必然有回指。
  **When to use**：让读者知道"从这儿还能去哪儿"，同时让断链无处藏身。
- **路径限定单段式链接**：全库统一 `[[topics/xxx]]` 形式，不用 `[[显示名|目标]]`。
  **When to use**：需要跨工具（Obsidian / GitHub Wiki / 检索系统）都能解析时。
  **How**：写相对路径的全限定名，把显示文字放到链接外的正文里。
- **元文件改名而非删除**：`README.md` / `index.md` / `log.md` / `schema.md` / `RESOLVER.md`
  会被检索系统当"元文件"跳过——改名，映射留档。
  **When to use**：入库前发现某些文件没被收录时。

## Key Concepts
- **原文层（Source layer）**：`01-` ~ `20-`，20 个上游来源，一字不改
- **主题层（Topic layer）**：`topics/`，11 篇中文原创消化页
- **索引层（Index layer）**：`index/`，4 篇导航页
- **双链（Bidirectional link）**：页面间的 wiki 链接，构成本地知识网络
- **slug**：相对路径去掉扩展名后的小写折叠形式，是检索系统里的页面身份
- **元文件（Metafile）**：被检索系统默认跳过的约定文件名
- **回指（Backlink）**：指向本页的入链

## Mental Models
- **图书馆模型**：原文层是书架上的书，主题层是图书馆员写的卡片（不抄书的内容，
  只告诉你这本书讲什么、在哪一页），索引层是门口的目录。
  **推论：卡片过期了可以重写，书不会因此被改坏。**
- **证据链要能一直指回源头**：任何一个结论都应该能顺着指针走到原文——
  走不到的结论就是"没出处的话"。

## Anti-patterns
- **在主题层里复制原文长段**：一份内容两处维护，迟早不一致。
- **用别名式链接 `[[A|B]]`**：同一个语法在 GitHub Wiki / Obsidian / 检索系统里
  **含义相反**（有的把竖线前当目标，有的当显示名），混用必然产生断链。
- **把元文件当正文删掉**：应该改名，不是删除。
- **主题页之间不互反**：单向边会让"相关页面"变成单向可达的残缺网络。

## Code Examples
双链图谱（摘自 `index/knowledge-map.md`）——手写维护的主题层拓扑：

```
                    ┌──────────────────────────┐
                    │  index/knowledge-map     │ ← 入口
                    └────────────┬─────────────┘
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
   index/sources        index/learning-path         index/cases
         └───────────────────────┼───────────────────────┘
                                 ▼
   ┌───────────────────── topics/ ─────────────────────────┐
   │  ownership-and-lifetime ◄──► move-semantics             │
   │        │  ▲                   │      ▲                  │
   │        │  └── pitfalls ◄────────┘      │                  │
   │        ▼                               ▼                  │
   │  stl-containers-algorithms ◄──► templates-and-concepts   │
   │        │  ▲                         ▲                    │
   │        ▼  │                         │                    │
   │     concurrency ◄────────► performance                   │
   │        │                        ▲                       │
   │        ▼                        │                       │
   │   error-handling ──► pitfalls ───┘                       │
   │        ▲                                                │
   │        │                                                │
   │  modern-cpp-features ◄──► project-practices             │
   │        ▲                      │                         │
   │        └──────────────────────┴──► toolchain-and-debugging
   └──────────────────────────────────────────────────────────┘
```

## Reference Tables

**目录结构**

```
knowlege/
├── README.md              ← 给人的前门（与 knowledge-map 内容相同）
├── index/                 ← 索引层
│   ├── knowledge-map.md   知识地图（枢纽）
│   ├── sources.md         20 个来源清单：作者/许可/star/commit/适用场景
│   ├── learning-path.md   四阶段学习路线
│   └── cases.md           案例索引
├── topics/                ← 主题层（中文原创）
│   ├── ownership-and-lifetime.md   所有权与生命周期
│   ├── move-semantics.md           移动语义与完美转发
│   ├── templates-and-concepts.md   模板与 Concepts
│   ├── stl-containers-algorithms.md STL 容器与算法
│   ├── concurrency.md               并发编程
│   ├── error-handling.md            错误处理
│   ├── performance.md               性能优化
│   ├── modern-cpp-features.md       现代 C++ 特性全景
│   ├── project-practices.md         工程实践
│   ├── toolchain-and-debugging.md   工具链与调试
│   └── pitfalls-and-antipatterns.md 陷阱与反模式
├── 01- … 20-              ← 原文层（20 个上游来源）
└── _meta/                 ← 下载脚本、规则索引、校验器、评测报告
```

**三层职责对照**

| 层 | 目录 | 内容 | 变更频率 | 谁维护 |
|---|---|---|---|---|
| 原文层 | `01-` ~ `20-` | 上游仓库原文，一字不改 | 低（随上游更新） | 抓取脚本 |
| 主题层 | `topics/` | 中文原创消化页，11 篇 | 中 | 人工 |
| 索引层 | `index/` | 导航与台账，4 篇 | 低 | 人工 |

## Worked Example
**一次跨层查询：「`std::remove` 到底删不删元素？」**

1. **入口层（`index/knowledge-map.md`）**："快速知道这条 C++ 代码该怎么写才不踩坑"
   → 指向 `[[topics/pitfalls-and-antipatterns]]`。
2. **主题层（`topics/pitfalls-and-antipatterns.md`）**：第二章直接给结论——
   `std::remove` 只做移动，`size` 没变；正确写法是 `v.erase(std::remove(...), v.end())`；
   并且警告它和 `std::filesystem::remove` 同名不同义。末尾"出处"指向
   `../01-core-guidelines/CppCoreGuidelines.md` 与 `../03-best-practices/09-Considering_Correctness.md`。
3. **原文层（`01-core-guidelines`）**：搜 `std::remove` 在规则原文里的示例段落，
   确认"算法只移动、删除要另配 `erase`"这个措辞的权威出处；
   配套原则是 ES.1（"优先用标准库而不是手写代码"）。
4. **回到主题层查细节**：`topics/stl-containers-algorithms.md` 里有 `erase-remove` 惯用法
   的完整写法与迭代器失效表。
5. **验证**：`scripts/kb_lookup.py "std::remove erase"` 两条命令就能定位到上面第 2、4 步的页面。

全程没有复制任何原文长段，每一步都能指回源头——这就是三层结构的收益。

## Key Takeaways
1. 三层职责：原文是证据，主题是索引，索引是入口。
2. 主题层每页结构固定为「结论 → 规则 → 案例 → 坑 → 出处」——出处是硬要求。
3. 双链必须互反，单向边会让网络残缺。
4. 链接一律用路径限定单段式 `[[topics/xxx]]`，别用别名式（跨工具语义相反）。
5. 元文件改名不删除，映射公开留档。
6. 进库前先看该文件是不是元文件——否则会"明明下好了却搜不到"。

## Connects To
- **Ch12**: 案例索引——索引层的一员
- **Ch13**: 学习路线——索引层的一员
- **Ch14**: 来源台账——索引层的一员，也是原文层的台账
- **Ch01–Ch11**: 主题层各章——本库的实质内容
