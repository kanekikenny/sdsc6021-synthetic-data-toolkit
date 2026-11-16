# 100 图标注接收与一致率

2026-11-16 已收到两份完整标注表。两份各有 100 行，对应同一批预抽样候选图，每类 10 张。编号、目标类别和图片路径与原标注包一致；图片字节也与原包一致。原 Excel 留在本地运行审计目录，共享 CSV 保留填写者的判断和备注。

| 标注者代号 | 日期 | 用户报告用时 | correct | wrong | uncertain | 非空备注 |
|---|---|---|---:|---:|---:|---:|
| A | 2026-11-16 | 约30分钟 | 100 | 0 | 0 | 30 |
| D | 2026-11-16 | 半小时 | 100 | 0 | 0 | 24 |

## 统计结果与范围

- 两份表的类别判断一致：100/100，观察一致率为 **100%**，没有判断分歧；十个类别各为 10/10。
- 两份均只使用 `correct`。Cohen's kappa 在这个特例中未定义：按两份表的类别边际比例计算，预期一致率也是 1，公式分母为 0。因此结果保存为 `null`，不填成 1。
- `correct` 表示目标类别清楚可辨，允许同时存在结构失真。这个结果不表示所有图片整体质量合格，也不直接推广到整个 2,000 图候选池。
- 备注是可选的自由文本。30 条和 24 条反映各人的记录，不作为缺陷率或备注一致率；原文均保留。
- 本次程序核验内容、样本对应及统计，不能单靠文件证明填写过程的独立性。非作者试用仍待实际执行；标注结果不改变训练图片、模型或正式预测。

## 给 C / D 的文件

| 文件 | 内容 |
|---|---|
| [annotator_1.csv](annotator_1.csv) / [annotator_2.csv](annotator_2.csv) | 两份原始逐图判断及备注 |
| [annotator_1_intake.json](annotator_1_intake.json) / [annotator_2_intake.json](annotator_2_intake.json) | 各自接收记录、代号/日期/用时、源 Excel 和 CSV 校验值 |
| [agreement.json](agreement.json) | 一致率、判断计数、分类别结果、分歧列表和统计限制 |
| [paired_annotations.csv](paired_annotations.csv) | 按图片编号对应的两份判断和原始备注 |
| [agreement_validation.json](agreement_validation.json) | 原表与导出内容核对、临时副本检查及冻结实验保护记录 |
| [说明.md](说明.md) | 统一判断规则与 note 填写说明 |

首份接收记录保留当时“第二份未接收”的状态；当前整体状态以本页、[human_materials.json](../human_materials.json)和根目录 progress.md 为准，不改写历史快照。

C 可使用[统计脚本](../../../../code/audits/17_human_label_agreement.py)复算，输出到自己的独立目录：

```text
python code/audits/17_human_label_agreement.py --first shared/synthetic_v2/audits/human_annotations/annotator_1.csv --second shared/synthetic_v2/audits/human_annotations/annotator_2.csv --out runs/_cache/human_agreement_recheck
```
