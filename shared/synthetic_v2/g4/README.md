# G4 正式预测交接给 C

正式评估已在 A 的 RTX 5070 Ti Laptop GPU 上完成。评估运行 `20261115T133443_199162Z`，执行代码 `26e107feba6c4c4c5f447f84cada707e140d738c`；实验源码和配置与原冻结版本一致，15 个训练模型及其封存清单均未改动。

这次交接包含正式预测和工程校验。C 的独立统计、四图四表及英文解释现已验收，见 [C 结果入口](../c_evaluation/README.md)和[验收记录](../audits/c_pr4_acceptance.json)；两份100图标注已接收并核验，见[标注结果入口](../audits/human_annotations/README.md)，类别判断一致率100%；非作者试用待接收。唯一实验规则仍见根目录 agent.md，实际分工与进度见 progress.md。ZIP 内的状态描述保留其原始交接时刻，不改写原文件。

`models/frozen.json` 的未评估标记描述 G3 封存时刻；保持该文件原字节以验证封存哈希。当前正式测试状态以本次 report.json、evaluation/latest.json 和验证记录为准。现有 summarize 的终端返回字段 test_evaluated 仍显示旧值 false，共享摘要已按实际报告更新；这项导出显示问题不改变正式预测或模型，也不作为重新评估的理由。

## C 现在下载什么

打开 [G4 Release](https://github.com/kanekikenny/sdsc6021-synthetic-data-toolkit/releases/tag/g4-official-evaluation-v0.4)，下载 `g4_predictions_and_run_records.zip` 和 `SHA256SUMS.txt`。准确位置、文件大小与 SHA-256 见 [delivery.json](delivery.json)。解压到自己电脑的独立数据目录即可做统计，无需 GPU 或重新生成/训练。

```powershell
gh release download g4-official-evaluation-v0.4 --repo kanekikenny/sdsc6021-synthetic-data-toolkit --dir deliverables/g4_synthetic_v2
Get-FileHash -Algorithm SHA256 deliverables/g4_synthetic_v2/g4_predictions_and_run_records.zip
Expand-Archive deliverables/g4_synthetic_v2/g4_predictions_and_run_records.zip -DestinationPath runs/g4_c_analysis_input
```

已有目标目录时先保留原文件，不覆盖。没有 gh 可从 Release 页面直接下载。校验值应与 delivery.json 和 SHA256SUMS.txt 一致。

## 包里有什么

| 路径 | 用途 |
|---|---|
| `exports/predictions_long.csv` | C 优先读取的完整长表，共 160,000 行：15 个分类器 × 10,000，加一次 CLIP 参考 × 10,000 |
| `evaluation/20261115T133443_199162Z/predictions/*.json` | 16 份原始正式预测，保留运行原路径和哈希 |
| `evaluation/20261115T133443_199162Z/report.json` | 原始评估报告、逐条件/seed 及分类别指标、阶段耗时、预测 SHA-256 |
| `evaluation/20261115T133443_199162Z/features/` | 测试特征索引和冻结证明；测试只使用基础视图，包内不包含特征数组或原始测试图片 |
| `evaluation/20261115T133443_199162Z/manifests/clip_scores.json` | 官方测试图的十类 CLIP 概率，打分函数没有接收测试真值 |
| `models/frozen.json`、`protocol.json` | 绑定原 15 个分类头的封存证明和配置；分类头文件在已有 G3 Release |
| `handoff/invocation.json`、`handoff/console.log` | 实际命令、环境、GPU/驱动、UTC 起止时间、退出码和控制台记录；解释器绝对路径已隐去 |
| `handoff/prediction_index.json`、`verification.json`、`file_index.json` | 样本数量、类别映射、CSV/JSON 文件及 SHA、工程复核记录 |

CSV 列为 `sample_id, condition_id, seed, true_label, predicted_label, prediction_split, config_hash`。所有行的 prediction_split 都是 official_test；sample_id 的数字后缀为官方 test_batch 中从 0 开始的行索引。类别 ID 顺序为 airplane/automobile/bird/cat/deer/dog/frog/horse/ship/truck。

CLIP 行的 condition_id 为 clip_zero_shot，seed 留空；它只评估一次，不参与五条件 × 三 seed 的均值/标准差计算。原始 JSON 与 CSV 已核对，所有文件使用相同 10,000 个测试 ID 和真值，每类 1,000 张。

## 已验收的 C 交付及复算口径

1. 从逐图预测重新计算每个 condition/seed 的 top-1 accuracy，并与原报告核对；结果不依赖报告中已经算好的数值。
2. 五个训练条件分别报告三 seed 均值和样本标准差（ddof=1）；提升先按同 seed 减去 real_only，再转为百分点，报告三个提升的均值及标准差。
3. 交五条件主表、三个 seed 的点图、配对提升及分类别分析。CLIP 零样本参考作为单次替代方案单独展示。
4. 结合已有 G3 [阶段成本](../stage_costs.json)和本次 [运行记录](invocation.json)汇总成本；特征阶段、CLIP 阶段与总墙钟有包含关系，不能相加重复计费。总评估约 219.36 秒；CLI 含启动约 221.52 秒，原始记录保存未四舍五入值。
5. 提交自己的计算脚本、实际复核记录和结果解释；源码放 code/audits/，必要小型结果/图表放 shared/synthetic_v2/g4/ 的清楚命名文件，原始大型产物留 runs/ 或交付附件。已验收的结果解释见 [C 的英文结果稿](../../../report/C_results_evaluation.md)，最终课程报告由 D 根据实际交付内容统稿。

可以在自己的 fork/模块分支提交 PR，由 A 集成。冻结训练源码和配置保持不变，不用正式测试表现修改参数、选图或重新训练。两位真人标注及非作者试用按独立安排记录，不用这些预测代替。
