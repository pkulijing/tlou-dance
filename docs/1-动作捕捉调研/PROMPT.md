> 来自 [#2 \[Spike\] 从《心愿便利贴》舞蹈视频中提取人物动作 (motion capture) 的可行性调研](https://github.com/pkulijing/tlou-dance/issues/2)
> Labels: `type:feat` `area:motion-extract` `priority:P0`

## 背景

本项目最终目标是做一段「TLOU 主角跳《心愿便利贴》」的整活视频，由两条互相独立的可行性闸门把守：

1. **asset-extract**：从本地《The Last of Us》游戏安装中拿到主角人形模型（round 0 同步进行中）
2. **motion-extract**（即本轮）：从浪姐 7 李小冉组《心愿便利贴》舞蹈视频中拿到能驱动 3D 人形 rig 的动作序列

任何一条不通整个项目就停摆，因此两轮都打 `P0`。本轮在独立的 worktree（分支 `round/1-motion-extract`）上推进，与 round 0 物理隔离。

## 待回答的核心问题

能否从《心愿便利贴》舞蹈视频（**多人同框、相机切换、有遮挡**）中提取出一段**可驱动 3D 人形 rig** 的动作序列？

「可驱动」的判定标准：选 10 秒典型片段，输出 BVH / FBX / SMPL 等通用动作格式，retarget 到一个简单 humanoid rig（先用 Blender 自带 mannequin 或 Mixamo 标准骨架）后，**肉眼可辨为原舞蹈动作**——无明显抖动、穿模、关键关节失衡。

## 验证目标 / 出口指标

- [ ] 选定一个 SOTA 单目视频 mocap 方案（候选见下「方法」段）
- [ ] 跑完一段 10 秒 clip，输出标准动作格式（BVH / FBX / SMPL 任一）
- [ ] 在 Blender 中 retarget 到简单 humanoid rig 上，渲一段播放视频
- [ ] 出 SUMMARY.md，给出**结论**：本路径在多人 + 切镜场景下是否可行；如不可行，记录失败模式 + 备选路线

## 方法

候选方案（按近年常见度 + 是否对多人/切镜友好排序）：

- **4D-Humans**（PHALP + HMR2.0 系列）：自带多人 tracking + 跨切镜 ID 维持，看起来对本场景最对路
- **WHAM**：world-grounded、运动质量高，但默认偏单人
- **SMPLer-X**：whole-body（含手指/表情），全身参数化输出
- **VIBE / TCMR**：经典基线，可作 fallback
- **HybrIK**：解析-反向-混合方法，关节准度好

策略：优先调研 **4D-Humans**（多人 + 切镜友好），如门槛过高（依赖、显卡显存、conda 环境冲突）退到 SMPLer-X 或 WHAM 单人模式 + 手动选片段。

## 范围与约束

- **时长上限**：2 天。只验证可行性，不追求最终质量。
- **片段长度**：10 秒，从《心愿便利贴》中挑一段李小冉镜头较稳、遮挡较少的部分作为「友好样本」。如友好样本能跑通，再尝试一段切镜复杂的「困难样本」对比。
- **不做**：不做最终视频渲染、不做风格化、不调参冲精度、不做手指/表情。
- **环境**：本地 GPU 跑（具体型号在 PLAN.md 中确认）；优先 docker/conda 隔离，避免污染项目 uv 环境。

## 预期产出

- `docs/1-动作捕捉调研/SUMMARY.md`：方案选型、踩坑记录、对**多人+切镜**的可行性结论、备选路线建议
- 一段 10 秒原视频片段 + 提取出的 SMPL/BVH/FBX 动作文件
- 一段 retarget 到 mannequin rig 后的播放视频
- 必要的调试脚本 / Blender 场景文件归到本轮 docs 文件夹的 `assets/`（或按 PLAN.md 决定的位置）

## 关联

- 并列闸门：[#1 asset-extract spike](https://github.com/pkulijing/tlou-dance/issues/1)（round 0，独立 worktree）
- 收尾时 commit/PR 描述写 `Closes #2` 自动关 issue
