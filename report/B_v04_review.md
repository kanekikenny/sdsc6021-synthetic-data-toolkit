# B：冻结 0.4 版本复核与方法交付

后续交付（2026-11-16）：已完成对 C 正式 G4 统计的独立交叉复核，见 [B/C 统计复核报告](B_C_G4_cross_review.md)。本文件保留原训练/特征复核范围及失败，不把后续统计通过解释为严格特征匹配通过。

本次以 A 当前主分支 `26e107f` 和正式执行提交 `c576316` 为准。旧 B 开发基线保留为历史；其划分、200 次全批量更新及未归一化特征不用于本次复核。正式设置完全沿用 `configs/study.json`，未修改冻结执行源码、参数、封存模型或特征。

## 实际完成

| 复核项 | 实际观察 |
|---|---|
| 下载与还原 | `training_bundle.zip` 30,208,113 字节，SHA-256 与 Release 一致；包内索引的 3,001 个文件大小和校验值通过 |
| 数据与标签 | 三个 seed 各 200 张、每类 20 张；598 张不同真实图片的像素及标签与校验过的官方训练批次一致；抽样顺序独立重算一致 |
| 特征与输入映射 | 2598×4×512，float32、有限值、L2 范数、行号/图片 ID/类别/原图哈希及全部条件的输入对应通过 |
| 筛选输入 | random/CLIP 各每类50和150张，无重复，50张嵌套在150张集合内；选择文件与封存哈希一致 |
| 15 个分类头 | 文件和配置核对通过；配对初始化、真实批次独立重算通过；从初始化重新执行每头500次SGD，共7,500次更新 |
| 数值重训 | 最大权重差4.7684×10⁻⁷，未超过预先设定的10⁻⁶；重载预测与包内全部3,000条记录一致 |
| 实际冻结复核 | 在本机重新提取全部598张真实图的2,392个视图，骨干完整状态及BN缓冲均未改变 |
| 特征严格数值复现 | **未通过**：CPU与A的GPU特征最大绝对差0.00020127，超过原定0.00001；阈值未放宽，失败记录保留 |
| 特征差异的预测影响 | 最小余弦相似度0.99999970；15个封存头各200张训练参考图，改用CPU重提取特征后的预测变化为0/3,000 |
| 原文件保护 | 复核前后全部封存输入校验值一致，21项现有协议检查通过；没有读取官方测试标签 |

## 待 A 确认的数值差异

本机为 Python 3.13.9、torch/torchvision 2.9.1+cpu/0.24.1+cpu；A 原环境为 Python 3.12.14、对应 cu128 构建。CPU复核不声称与原CUDA环境等同。

CPU和GPU的浮点输出可能不同，PyTorch不保证跨平台逐位一致；卷积精度及TF32可能相关。这只提供一种可能解释，**本次未直接测量A的后端精度开关，尚未确认根因**。[PyTorch 数值精度说明](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html)

建议 A 在独立诊断目录记录 torch、cuDNN、matmul/卷积精度设置、输入张量及相同批大小，对同一份真实图片重提取并与封存缓存比较；如需比较不同精度模式，应标为诊断输出。保持原封存模型、缓存、选择及配置不变，不能用最终测试效果选择精度或重训。

本次状态为 `completed_with_feature_numerical_finding`，不写成“全部复现通过”。该差异在训练参考图上未改变预测，不能外推为官方测试集上的一致性。

## 可整合到报告的数据与分类方法（英文）

For each seed in {0, 1, 2}, we select 20 training images per CIFAR-10 class using a deterministic class-wise permutation of official training indices. The same 200 real images are shared across all five conditions within a seed. Formal training has no development subset. Across the three seeds there are 598 distinct real originals; together with 2,000 synthetic candidates, these give a portable feature tensor of shape [2598, 4, 512]. Official class IDs, original indices, image hashes and feature-row identities are retained.

The ImageNet V1 ResNet-18 backbone remains frozen in evaluation/inference mode, including its BatchNorm buffers. Each original contributes one weight-prescribed base view and three fixed-seed augmented views. Augmentation uses random resized crops of size 224, scale [0.7, 1.0], aspect ratio [0.75, 4/3], horizontal flipping probability 0.5 and ImageNet normalization. The 512-dimensional features are L2-normalized. Only the ten-class linear classification head is optimized.

Each head uses 500 SGD updates with learning rate 0.1, momentum 0.9 and weight decay 0.0001. Each source contributes two sampled originals per class per update, with replacement. The per-source loss averages four view losses within each original before averaging originals. Mixed conditions use equal real/synthetic source weights of 0.5; the real-only baseline uses the real-source mean alone. Initial head state and the real-sample schedule are paired across conditions within each seed.

A separate B-side CPU implementation verified the official training pixels, labels, sampled indices, feature mapping and model files, then replayed all 15 optimization trajectories. Maximum head-weight error was 4.77e-7, within the predefined 1e-6 tolerance, and all 3,000 saved training-reference predictions agreed. Re-extraction of all real-image views preserved the backbone state and BatchNorm buffers. However, CPU/GPU feature differences exceeded the strict 1e-5 absolute threshold (maximum 2.01e-4). This numerical finding remains recorded; no threshold was relaxed. Predictions on the 3,000 training-reference checks were unchanged when using the CPU-recomputed base features. These checks establish implementation and artifact consistency within the stated limits, not test-set performance or synthetic-data utility.

## 实际贡献与范围

GitHub 账号 careless-Snow 提交本 B 角色复核；其真实姓名/学号及与组员的对应尚待确认。本次检查脚本、运行和文字由 Codex 协助完成，不声称提交者本人手动执行或存在第二位真人复核者。21项检查、完整结果和初次失败记录见 `shared/b_v04_review/`。

合成原图归档未下载，合成特征只进行了封存完整性和输入映射复核，未重提取全部2,000张合成图片。整合时 G4 正式预测及 CLIP 零样本已由 A/Codex 在约定环境完成并发布；C 接续独立统计和图表，真人标注和非作者试用仍需实际人员执行。

## A 整合时的补充诊断

原始数值阈值、失败和 B 全量复核状态保持不变。A 随后使用 seed0 第一完整训练批次（8 图、32 视图）固定输入进行受控诊断：默认 CUDA 输出逐位复现封存缓存；CPU 最大差约 1.02e-4；关闭 cuDNN TF32 后 CUDA/CPU 最大差约 7.45e-7。该证据支持这批训练样本上的后端精度解释，不使全量严格匹配改判通过，不证明测试集预测一致。原模型、缓存和 G4 结果均未变，未按测试表现选择精度。[原始诊断记录](../shared/synthetic_v2/audits/b_pr3_precision_diagnostic.json)。
