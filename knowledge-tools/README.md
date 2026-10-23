# 知识库工具（可选）

本目录是 `knowlege/` 知识库的**可复现工具**，不是知识库本体。
知识库本体约 1GB（20 个上游仓库的原文快照），独立维护，不进本仓库。

## 文件

| 文件 | 作用 |
|---|---|
| `extract-rules.py` | 从 `knowlege/01-core-guidelines/CppCoreGuidelines.md` 原文重建规则清单 |
| `core-guidelines-rules.txt` | 重建产物：500 条规则的「编号: 标题」清单，是 `skill-c++/references/rule-index.md` 的真源 |
| `sources.tsv` | 20 个上游来源台账（作者 / 许可 / 用途） |
| `retrieval-eval.py` | 知识库检索评测（18 问），量化「精确提问 vs 宽泛提问」的召回率 |
| `retrieval-eval.md` | 上一轮评测基线结果 |
| `check-links.py` | 知识库内部双链完整性检查 |

## 什么时候需要它

只有在你**自己也建了同规格的知识库**时才需要。
直接使用 `skill-c++` 的人不需要它们——skill 自带
`references/rule-index.md`（同一份清单的生成副本），
没有知识库也能做规则号校验（`rule_lint.py` 会自动回退到它）。

## 用法

```bash
python extract-rules.py --check        # 只比对，不写文件
python retrieval-eval.py               # 跑检索评测
python check-links.py                  # 查双链完整性
```
