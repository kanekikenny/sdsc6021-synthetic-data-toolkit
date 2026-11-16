# 五分钟演示讲稿与换人安排

只讲第1–8页，第9–12页仅用于问答。英文正文437词，计划270秒，含各页停顿与换人预算；实际时长仍需真人排练。建议保持约110词/分钟或更快的自然语速。4:30前进入收尾，4:50结束，最晚5:00停止。

正文页脚标A/B/C/D为建议讲述负责人，最后一页按用户确认的分工表列职责；它不代替实际贡献证明。姓名/学号和老师指定封面信息尚未提供，不虚构。

| 页 | 内容 | 负责人 | 分配秒数 | 累计结束 |
|---|---|---|---:|---|
| 1 | Problem and toolkit | D | 20 | 0:20 |
| 2 | Recorded workflow | A | 35 | 0:55 |
| 3 | Controlled protocol | B | 45 | 1:40 |
| 4 | Formal classification results | C | 45 | 2:25 |
| 5 | Quantity, selection and cost | C | 30 | 2:55 |
| 6 | Zero-shot alternative | C | 35 | 3:30 |
| 7 | Human audit and author self-test | D | 35 | 4:05 |
| 8 | Contribution, limits and responsibilities | D | 25 | 4:30 |

超过计划时：第5页只读“更多保留图无额外均值收益”；第8页职责已在表中展示，不逐项展开。备份页完全跳过。不得用删掉CLIP参考、作者自测限制或损失权重口径来压缩时间。

## Slide 1: Problem and toolkit

负责人 D，目标20秒。

Our project asks whether generated training images help when real labels are limited. We built a toolkit that generates class images, trains matched classifiers and checks their performance on real test data. We demonstrate it with twenty real images per class.

Sources: agent.md, configs/study.json

## Slide 2: Recorded workflow

负责人 A，目标35秒。

The input is a class list and a small real training set. Stable Diffusion generates candidates. We select images, extract frozen features and train linear classifiers. The outputs include saved models, predictions and compute records. Our recorded run produced two thousand candidates and fifteen classifiers. The release preserves the data and settings needed to audit the result.

Sources: shared/synthetic_v2/README.md, shared/synthetic_v2/g4/README.md, https://arxiv.org/abs/2112.10752

## Slide 3: Controlled protocol

负责人 B，目标45秒。

We compare real data alone with fifty or one hundred and fifty synthetic images per class, selected randomly or by CLIP. Three paired seeds share real samples, head initialization and real sampling. Every head uses five hundred updates. We freeze ResNet and BatchNorm. Mixed training gives equal weight to real and synthetic losses. This evaluates that mixing strategy, including its changed real-loss weight.

Sources: configs/study.json, code/classifier.py, report/B_v04_review.md

## Slide 4: Formal classification results

负责人 C，目标45秒。

On ten thousand real test images, the baseline reaches seventy-one point four four percent. The mixed conditions reach about seventy-five percent. Their average improvements range from three point six two to three point eight four percentage points. All three paired seeds improve. These results support a benefit for this classifier and setting. The displayed standard deviations describe seed variation, not confidence intervals.

Sources: shared/synthetic_v2/c_evaluation/tables/07_g4_summary.csv, report/C_results_evaluation.md

## Slide 5: Quantity, selection and cost

负责人 C，目标30秒。

CLIP selection adds only about zero point two percentage points over random selection. Keeping one hundred and fifty instead of fifty adds almost nothing. Recorded stages total about forty-eight minutes, dominated by generation. Both sizes share the same generated pool, so retaining fewer images does not save that generation cost. These small differences remain descriptive.

Sources: shared/synthetic_v2/c_evaluation/tables/13_g4_direct_comparisons.csv, shared/synthetic_v2/c_evaluation/tables/12_g4_cost_summary.csv

## Slide 6: Zero-shot alternative

负责人 C，目标35秒。

A useful tool must also reveal stronger alternatives. Zero-shot CLIP reaches eighty-eight point two one percent here. It uses a different pretrained model, so this is an alternative approach rather than a controlled augmentation comparison. Our result supports improving the fixed ResNet baseline. It does not establish the best practical classifier for this benchmark.

Sources: report/C_results_evaluation.md, https://proceedings.mlr.press/v139/radford21a.html

## Slide 7: Human audit and author self-test

负责人 D，目标35秒。

Two annotation forms agree that the target class is recognizable in all one hundred sampled images. Structural defects can still remain. Author testing passes the functional checks, but exposes a reading problem: the numbers are visible while their meaning is unclear. We added condition definitions and separate loss terms. External user usability remains untested.

Sources: shared/synthetic_v2/audits/human_annotations/README.md, shared/synthetic_v2/audits/author_self_test/README.md

## Slide 8: Contribution, limits and responsibilities

负责人 D，目标25秒。

Our contribution is a reproducible toolkit and a controlled case study. Prior work already studies synthetic augmentation. Our evidence covers one dataset, one label budget and a shared generation pool. The team divides engineering, classification, evaluation and product delivery as shown. The toolkit helps inspect both the gains and the limits.

Sources: 分工.md, progress.md, https://arxiv.org/abs/2210.07574

## 交付说明

PPTX含可编辑图表、表格及每页英文讲者备注。PDF含8页正文和4页备份，演示到第8页结束。作者自测核验已有记录，未新增正式实验重复；非作者试用未完成。课程技术报告仍由D另行统稿。

本套材料由Codex在A授权下整理，数据和队友复核归属沿用项目记录。四人上台前应核对本人实际贡献并做一次计时排练。
