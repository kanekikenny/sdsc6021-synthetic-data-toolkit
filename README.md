# SDSC6021 — Synthetic Data Toolkit

面向 20-shot 图像分类的合成数据增强工具：生成补充图片、选择样本、训练分类器，并评估真实测试效果。

> 当前：G4 正式评估与预测交接已完成。15 个封存分类器和一次 CLIP 参考共 160,000 条正式测试预测，连同运行记录已公开并验证下载。[C 的 G4 数据入口](shared/synthetic_v2/g4/README.md)说明约 4 MB 预测包的下载、字段和后续统计任务；[G3 入口](shared/synthetic_v2/README.md)保留图片、特征与模型。C 的独立分析、4图、4表及英文结果稿已验收合并，见 [结果入口](shared/synthetic_v2/c_evaluation/README.md)。首位标注者的 100 图判断已接收，见[标注记录](shared/synthetic_v2/audits/human_annotations/annotator_1_intake.json)和[备注说明](shared/synthetic_v2/audits/human_annotations/说明.md)；第二位标注、非作者试用及最终报告/展示统稿待完成，实际进度见 progress.md。

## 阅读入口

- [agent.md](agent.md)：唯一项目规则，包含实验协议、数据接口、GitHub 共享范围、验收及报告框架。
- [progress.md](progress.md)：唯一实际进度，包含证据、待办、阻塞和成员分工。
- [队友接手清单](progress.md#队友现在需要做什么)：B/C/D 现在需要取什么、完成什么，以及哪些任务使用 A 的 GPU 电脑。
- [G4 正式预测与运行记录](shared/synthetic_v2/g4/README.md)：原始数据与运行证据。
- [C 正式分析、CSV 和四张结果图](shared/synthetic_v2/c_evaluation/README.md)及[英文结果稿](report/C_results_evaluation.md)：已验收的统计交付，D 可接手统稿与展示。
- [B 独立复核](shared/b_v04_review/README.md)与 [C 选择/统计规则审计](shared/synthetic_v2/c_independent_audit.md)：已合并的队友成果；B 数值差异和原阈值保留，C 的真实预测分析与图表见下方结果入口。
- [B 对 C 正式 G4 统计的交叉复核](shared/b_c_g4_review/README.md)：PR #5 已实际复跑验收，16万条预测及四表250个数值项核对通过；原严格特征复现限制保留。
- [团队分工](分工.md)：A–D 工作包及必须交出的产物；具体成员认领和实际完成情况仍以 progress.md 为准。

本文件只用于入门导航；详细协议只维护在 agent.md，运行状态只维护在 progress.md。

## 团队协作

- 本仓库公开，队友可以直接查看和克隆；直接推送仍需协作者权限，也可通过 fork 提交 PR。代码、配置和 Markdown 文档以本仓库为唯一共享来源。
- 各人在模块分支提交小范围修改，A 负责集成，D 汇总进度和报告；具体认领状态见 progress.md。
- 先按 agent.md 约定接口，用小样例并行开发，再进行完整试跑。正式测试统一使用 A 的 GPU；队友有兼容 CUDA 环境时，开发、试跑和独立复核优先用自己的电脑。同一台机器的 GPU 作业顺序排队，详见 agent.md 的“运行分配”。
- 每个模块作者编写对应报告内容；代码作者、实际运行者和写作者分别记录。

## 文件共享

- **提交仓库：**项目文档、代码、可执行配置与依赖清单（实现后）、报告/展示源稿、必要的小型结果与图表。
- **本机保存：**runs/ 原始产物、完整图片、特征、模型权重、环境和下载缓存；重要产物另做备份。
- 队友需要的图片、便携特征和分类头通过同仓库 GitHub Release 交接；共享位置和 SHA-256 登记在 shared/<run_id>/，不另外复制一套代码。详细入口见 [G3 交接说明](shared/synthetic_v2/README.md)。
- 课程课件及要求摘录保留本地，不纳入上传范围。详细共享清单与交接责任见 agent.md。
- 文件目录、临时文件、备份及推送前后检查统一遵循 agent.md 的“文件管理与 GitHub 同步规则”，不另建管理规范。

## 开始工作

依次阅读 agent.md 和 progress.md。[G1 环境检查摘要](shared/g1_environment/check.json) 保存当时的模型文件校验、实际推理结果及限制；当前代码及 G2 状态以 progress.md 为准。

[当前 0.4 验收](shared/g2_smoke_20261115T100414_504102Z/check.json)及[生成参数与图片等价核验](shared/g2_smoke_20261115T100414_504102Z/revision_equivalence.json)保存本版证据；同目录有划分、分数、排名、选择及开发集预测。[样图 1](shared/g2_smoke_20261115T100414_504102Z/generation_classes_0_4.jpg) / [样图 2](shared/g2_smoke_20261115T100414_504102Z/generation_classes_5_9.jpg)供查看试跑输出，正式质量抽查与收益评估仍待后续执行。此前目录保留为版本历史。

已在本机独立环境验证的命令（本轮模型核验使用完整本地缓存，以 HF_HUB_OFFLINE=1 离线执行）：

```powershell
.\.venv\Scripts\python.exe code/toolkit.py doctor
.\.venv\Scripts\python.exe code/toolkit.py doctor --models
.\.venv\Scripts\python.exe code/toolkit.py plan
.\.venv\Scripts\python.exe code/toolkit.py smoke
.\.venv\Scripts\python.exe -m unittest discover -s code -p 'test_*.py' -v
```

环境使用 Python 3.12.14。重建时用 Python 3.12 创建 .venv，再依次安装 requirements-gpu.txt（官方 cu128 索引）和 requirements.txt（其余固定版本）；pip 命令加 --disable-pip-version-check。本机安装曾复用已有 CUDA 分发包，详细复制和校验记录保留在本地 runs/_cache/。

`doctor --models` 检查 SD1.5 出图、CLIP 打分与冻结 ResNet 特征；首次缺少缓存时需要下载权重。`smoke` 保留独立证据并复用经过校验的生成/特征缓存；`freeze --run-dir <本地试跑目录>` 接受完整检查和十类样图审阅通过的当前配置/代码。`select/features/train` 为正式阶段入口，`summarize` 导出正式共享快照，加 --run-dir 则导出指定 smoke。G4 的 evaluate --final 已在 15 个封存模型上执行成功；后续分析直接使用已发布预测，不利用测试结果调参或重训。
