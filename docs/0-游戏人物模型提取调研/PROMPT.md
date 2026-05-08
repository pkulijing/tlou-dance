# Round 0 — 游戏人物模型提取可行性调研

> 来自 [#1 \[Spike\] 从 The Last of Us 游戏安装中提取主角人物模型的可行性调研](https://github.com/pkulijing/tlou-dance/issues/1)
> Labels: `type:feat` `area:asset-extract` `priority:P0`

## 背景与需求

整个 tlou-dance 项目要让《The Last of Us》主角跳一段《心愿便利贴》舞蹈。这条流水线的输入端有两个门槛：「游戏人物模型 + 场景」与「视频动作」。本轮先攻前者。

**核心问题**：能否从本地 PC 安装的 The Last of Us 中提取主角（Joel / Ellie 等）的 3D 模型？资产格式、解包工具链、素材完整度（几何 + 骨骼 + 贴图）需要逐项确认。

**验证目标**：能在 Blender 里成功导入至少一位主角模型，看到带骨骼绑定（rig）的几何 + 贴图。

**判定标准**：导出后通用 3D 软件可读、骨骼可见可旋转、贴图正确显示。

## 方法

- 调研 TLoU（Part I 或 Part II，看本地装的是哪个版本）的资产打包格式
- 检索社区是否有开源解包工具（如 Special K / NinjaRipper / 专门的 TLoU 解包脚本）
- 跑一个最小样例：单个主角模型导出 → Blender 加载

## 预期产出

- 一份 SUMMARY.md：可行性结论、推荐工具链、踩坑记录、版权 / 许可注意点
- 一张 Blender 截图（含模型 + 骨骼）
- 如条件具备，1~2 个可用模型文件

## 关联

- **前置**：无
- **被阻塞的后续**：后续 motion-driven render 阶段（驱动模型跳舞）依赖本轮结论
- **并行 spike**：[#2](https://github.com/pkulijing/tlou-dance/issues/2) 视频动作捕捉调研

## Scope

时长上限 2 天；跑通最小路径就停，不追求全角色 / 全场景覆盖。
