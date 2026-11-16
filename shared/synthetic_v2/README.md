# G3 团队交接：synthetic_v2

协议 `0.4-frozen`，执行代码 `c5763166b2fe752e2257e7fb35039dc3ac1e0be7`；配置 SHA-256 为 `5380e7f962bb3646c6ff81148dd3d3ff2f96d1af97f008a774454af03eacd5ad`。

本页说明 G3 产物如何使用，项目规则仍以根目录 agent.md 为准。**G4 正式测试现已完成，[正式预测交接入口](g4/README.md)提供实际 CSV/JSON 及运行记录。**C 的独立统计/图表已验收；两份100图标注已接收并核验，类别判断一致率100%，非作者试用待接收；原 G3 Release 保留当时快照。

## 下载什么

[GitHub Release：G3 数据交接](https://github.com/kanekikenny/sdsc6021-synthetic-data-toolkit/releases/tag/g3-synthetic-v2-v0.4)。上传状态及精确下载地址以 [artifacts.json](artifacts.json) 为准；草稿不算已交付。

已发布的 16 个附件均通过匿名访问检查；训练包及校验清单已完整下载核对 SHA-256。[附件总索引](release_assets.json)记录文件大小、哈希和下载地址；[公开下载证明](public_download_check.json)记录实际检查。

| 附件 | 内容 | 谁需要 |
|---|---|---|
| `candidate_images_class_00.zip` 至 `09.zip` | 每类 200 张原始 PNG，共 2,000 张；编号沿用 CIFAR-10 官方类别顺序 | A 保管，B/C 检查数据时下载 |
| `training_bundle.zip` | `[2598,4,512]` 特征、15 个线性分类头、三组各 200 张真实训练图、划分/选择/逐图生成记录、重载预测与封存证明、失败及迁移历史 | B/C 优先下载，查看特征和模型不需要重新生成 |
| `label_audit_packet.zip` | 100 张预抽样图、两份空白独立标注 CSV 和判断说明；隐藏 CLIP 分数 | 两位真人标注者；请不要先看排名文件 |
| `SHA256SUMS.txt`、`G3_HANDOFF.md` | 附件校验值和本说明快照 | 所有人 |
| `stage_costs.json`、`handoff_restore_check.json` | 原始阶段耗时及独立解包/模型重载核验 | C/D |

图片来自生成模型，prompt 类别不保证真实正确。分类头是 512→10 的线性层，需要配置指定的 ResNet-18 特征及预处理；不是独立的完整图像模型。SD、CLIP 和 ResNet 供应方权重不随附件分发。

## 下载并还原

新克隆的仓库中执行；已有运行目录时先保留原记录，不覆盖。无需下载图片就能检查便携特征和分类头。

```powershell
git fetch --tags
# 复现实验时使用执行代码版本；编辑文档请使用 main 或自己的模块分支
git switch --detach g3-synthetic-v2-v0.4
gh release download g3-synthetic-v2-v0.4 --repo kanekikenny/sdsc6021-synthetic-data-toolkit --dir deliverables/g3_synthetic_v2
```

没有 gh 的成员可在上面的 Release 页面直接下载。下载全部附件后，在项目根目录核对哈希：

```powershell
$assetDir = Join-Path $PWD 'deliverables/g3_synthetic_v2'
foreach ($line in Get-Content (Join-Path $assetDir 'SHA256SUMS.txt')) {
    $entry = $line -split '  ', 2
    $actual = (Get-FileHash -LiteralPath (Join-Path $assetDir $entry[1]) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $entry[0]) { throw "Hash mismatch: $($entry[1])" }
}
if (Test-Path 'runs/synthetic_v2') { throw 'Run directory already exists; preserve it before restoring.' }
New-Item -ItemType Directory -Path 'runs/synthetic_v2' | Out-Null
Expand-Archive -LiteralPath (Join-Path $assetDir 'training_bundle.zip') -DestinationPath 'runs/synthetic_v2'
Get-ChildItem -LiteralPath $assetDir -Filter 'candidate_images_class_*.zip' | ForEach-Object {
    Expand-Archive -LiteralPath $_.FullName -DestinationPath 'runs/synthetic_v2'
}
```

仅下载部分附件时，用 artifacts.json 中该附件的 SHA-256 单独核对；上面的完整校验命令会要求所有文件存在。盲化标注包独立解压到其他目录，不混入正式运行。

## B/C 如何直接读取

`features/training_features.npz` 不需要 GPU：`x` 为 float32 特征、`image_ids` 为行对应 ID、`labels` 为官方类别 ID。第 0 个视图是基础视图，其余三个是固定增强。具体行映射也在 features/bundle_index.json。总行数为 2,000 合成 + 598 个不重复真实训练样本；三个 seed 各有 200 张，两张真实图在不同 seed 间重合，共享图的特征相同。

```python
from pathlib import Path
import json, numpy as np, torch

run = Path('runs/synthetic_v2')
with np.load(run / 'features/training_features.npz', allow_pickle=False) as data:
    x = data['x'].copy()
    ids = data['image_ids'].tolist()
    labels = data['labels'].copy()
checkpoint = torch.load(run / 'splits/seed0/models/real_only_seed0.pt',
                        map_location='cpu', weights_only=True)
head = torch.nn.Linear(512, 10)
head.load_state_dict(checkpoint['head_state'])
head.eval()
with torch.inference_mode():
    logits = head(torch.from_numpy(x[:4, 0]).float())
print(x.shape, ids[:4], logits.shape)
```

此示例只检查文件可用性，没有计算泛化准确率。训练重载预测明确标为 `train_reload_check_only`；不能作为正式测试结果。最终评估由现有唯一 CLI 的 `evaluate --final` 执行，绑定已封存的 15 个模型；不要改超参数或利用测试结果重新选图。

## 证据和待办

- [check.json](check.json)：G3 完成证据；[models/frozen.json](models/frozen.json)：15 个模型、输入及源码封存。
- [handoff_restore_check.json](handoff_restore_check.json)：所有图像归档、3,001 个包内文件校验、便携特征一致性、15 个模型输出复核。
- [stage_costs.json](stage_costs.json)：正式候选池生产约 42.52 分钟（含旧运行失败和恢复），选择约 39.97 秒、特征约 69.53 秒、15 个分类头约 8.42 秒。生成/特征使用单卡，分类头使用 CPU；不包含环境下载、G2、诊断、人工审阅、开发及传输，不能当作项目总耗时。
- 原失败日志和迁移关系保留；9 个安全标记均有绑定同一原图 SHA 的安全审阅记录。这不替代两人标签正确性抽查。
- 两份标注已接收：[标注结果入口](audits/human_annotations/README.md)提供A/D原始CSV、接收记录、100图配对表和一致率；类别判断一致100/100，备注分别30/24条，不代表整体质量均合格。[非作者试用模板](audits/non_author_trial_template.json)仍为空。
- [作者自测](audits/author_self_test/README.md)已记录工程复现和结果呈现问题，附只读事后诊断。原拟作非作者试用的操作经用户说明归为作者自测，不能计入外部用户验证；原始日志保留，完整用时缺失。
- 包内环境记录仅隐去原电脑解释器绝对路径，包版本与源码摘要保持原样。打包时的 `local_only_not_delivered` 描述当时状态；附件发布后的访问状态以本目录 artifacts.json 为准，不改写原始运行证据。
