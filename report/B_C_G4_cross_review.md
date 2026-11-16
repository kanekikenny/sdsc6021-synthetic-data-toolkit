# B 对 C 正式 G4 统计的交叉复核

日期：2026-11-16，香港时间。复核基线：`c70765015273bfbe4bf5bac859793c77bd497a65`；协议：0.4-frozen；run_id：synthetic_v2。

## 结论

本轮复核通过：从公开 G4 包内 16 万条逐图预测独立重算，C 的四份 CSV 共 64 行、250 个数值项全部在原表舍入精度内一致，未发现需修正的统计错误。四幅现有图的标签、点位、误差条和增减方向与结果一致。C 主实验结论可以用于最终统稿，但不能将三 seed 的描述性比较写成统计显著性结论。

这是 B 的统计交叉复核，由 Codex 协助实现、运行与写作；不冒充真人独立实验。没有重新生成、训练、执行 GPU 推理或修改配置。本轮会读取已发布的测试真值以复算最终指标，它与此前不读取测试标签的 B 训练复核分开记录。

## 实际核验

- 完整下载 3,980,356 字节 G4 预测包；SHA-256 为 `91045de3b946dccd21d9b6810f06309b1f86dc09ba4d814a158a4f9c078f6807`，匹配交付索引。
- 15 个分类器加一次 CLIP 参考；逐文件哈希、每份 10000 个唯一测试 ID、十类各 1000 条、跨文件真值及配置对应均通过。零样本原始文件只有三列，身份由带哈希的索引和报告绑定，不伪造 seed 或重复三次。
- 使用只依赖 Python 标准库的新工具 `code/reviews/review_c_g4.py`，不调用 A/C 的统计函数。正确数先计为整数，再转换百分比；每项比较按同 seed 相减，样本标准差显式使用 n−1 分母。
- 与 C 对照：主表 20 项，分类别表 200 项，直接对比表 20 项，成本表 10 项。主表/直接对比/成本容差为 0.00005，分类别为 0.0005，均仅对应现有 CSV 的四位/三位小数舍入，不是放宽实验复现阈值。
- 另与 A 的逐运行及分类别准确率核对一致；未另下载官方测试标签独立核对真值来源。
- 两个负面对照均被拒绝：循环错配真实基线 seed；把样本 SD 改成总体 SD。错配 seed 的平均提升可能不变，故同时检查三个配对提升及其 SD。
- 查看了四张已提交 PNG，并检查绘图数据来源与统计口径；本轮不重新绘图，不声称逐像素复现。四图均有清晰单位，误差条没有被称为置信区间；分类别图保留了 automobile/ship 的负值。

## 复算主结果

| 条件 | 准确率均值 ± 样本 SD（%） | 配对提升均值 ± 样本 SD（百分点） |
|---|---:|---:|
| Real Only | 71.4400 ± 0.3143 | 0 |
| Random 50 | 75.0800 ± 0.7370 | 3.6400 ± 0.8347 |
| CLIP 50 | 75.2800 ± 0.7627 | 3.8400 ± 0.7727 |
| Random 150 | 75.0567 ± 0.5845 | 3.6167 ± 0.6901 |
| CLIP 150 | 75.2600 ± 0.5769 | 3.8200 ± 0.6245 |

CLIP−Random 的均值差：50 张/类为 +0.2000 pp，150 张/类为 +0.2033 pp。150−50 的均值差：Random 为 −0.0233 pp，CLIP 为 −0.0200 pp。一次 CLIP 零样本参考为 88.21%，使用不同预训练模型，不能混入十五模型均值或包装为增强方法的公平替代对比。

五阶段记录合计约 2888.59 秒（48.14 分钟），生成占约 88.3%。这不是项目总工时；不重复计入 G4 CLI 墙钟，也不把共享生成池成本乘以十五。保留较少图片不代表原先生成整个候选池更便宜。

## 给 D 的统稿边界

1. 本设置的四种增强条件在三个配对 seed 上均优于真实基线，平均提升约 3.6–3.8 个百分点；不外推其他数据集、预算、骨干或生成池。
2. CLIP 筛选只表现出约 0.2 pp 的小幅描述性优势，50 张时 seed0 反而略低；增加保留数量未显示平均收益，不能写“数量越多效果越好”。
3. 原 B 特征严格复现失败（最大差约 2.01e-4，原阈值 1e-5）继续保留。有限训练样本上的 TF32 诊断不能变成全量跨平台通过；3000 条训练参考预测一致不能变成正式测试一致。
4. 当前主进度已经收到首位标注者100图结果，第二份和非作者试用仍待。C 结果稿的“尚未确认完成人工评估”应在最终统稿时结合最新记录表述为“首份已收到，双人审计及试用仍未完成”；无需改动历史提交或虚填一致率。
5. 本轮没有完成 B 对第二份图片的真人标注，也没有代替 D 进行最终统稿、演示或成员身份填写。

供 D 整合的英文复核表述：

> A separate B-side statistics review independently recounted all 160,000 released G4 prediction records using a standard-library implementation. All 250 numerical entries across the four C-side summary tables agreed within their published rounding precision. Matched-seed contrasts and sample standard deviations were verified; the results remain descriptive across three paired seeds. This review did not rerun GPU inference, resolve the previously documented full feature-reproduction discrepancy, or constitute human usability validation.

## 证据和复跑

结构化结果、三张全精度复算表、每运行计数及本次工具开发时的首轮格式错误说明见 [shared/b_c_g4_review](../shared/b_c_g4_review/README.md)。输入文件 SHA 和环境均保存在 `review.json`；原 ZIP 和本机控制台放在 `runs/b_c_cross_review/`，不进入 Git。

```text
.venv/Scripts/python.exe code/reviews/review_c_g4.py --bundle runs/b_c_cross_review/input/g4_predictions_and_run_records.zip --out runs/b_c_cross_review/results
```

只需 Python 3.10+ 标准库；本机实际使用已有 Python 3.13.9。下载地址和预期哈希取自 `shared/synthetic_v2/g4/delivery.json`。工具读取输入、不修改正式文件，输出请使用独立目录。
