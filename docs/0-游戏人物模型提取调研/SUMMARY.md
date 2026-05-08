# Round 0 — SUMMARY

> 来自 [#1 \[Spike\] 从 The Last of Us 游戏安装中提取主角人物模型的可行性调研](https://github.com/pkulijing/tlou-dance/issues/1)
> 结论：**通过**。三人模型现成可下载、统一骨架、Spike #2 启动条件就绪。

## 开发项背景

整个 tlou-dance 项目要让《The Last of Us》主角跳浪姐 7 李小冉组的《心愿便利贴》。流水线两端都有门槛：「角色模型」和「视频动作」。本轮就是前者的可行性 spike。

具体要回答的问题：

- 能否拿到 Joel / Ellie / Tess 三人的 3D 模型？（演员映射：王濛 ↔ Joel / 李小冉 ↔ Ellie / 唐艺昕 ↔ Tess）
- 几何 + 骨骼 + 贴图齐不齐？
- 能否进入后续动作驱动流程（即「单一动作数据可驱动多个角色」）？

## 实现方案

### 关键设计 1：Plan A（下现成 fan port）压倒 Plan B/C（自解包）

原计划从本地 PC 装的 TLoU Part II Remastered 自己解 .psarc + Noesis 导 FBX，意味着要切到 Windows 端 + 双 clone git 工作流。调研发现：

- [Crazy31139 在 DeviantArt](https://www.deviantart.com/crazy31139/gallery) 已经把 Joel / Ellie (Seattle) / Tess 三人 port 出 .fbx + .ascii + 分离 .dds 贴图，全部走 Yandex Disk 公开链
- 同一艺术家 → 同 ND 原骨骼 + 同 .dds 贴图风格 → 后续 retarget / 贴图 wiring 一套脚本套三人

收益：本轮预算从 2 天压到 1 天，省一次双 OS 切换；自解包工具链转为 fallback，仅 Plan A 失败时启动。

### 关键设计 2：剥光 ND 原 1500+ 骨骼，让 Mixamo Auto-Rigger 从零重建

ND 原骨骼命名是 `spinea / spineb / spinec / heada / headb / l_eyeball / ...`，**不符合 HIK / Biped 命名规范**，Mixamo 自动映射几乎一定失败。Adobe 官方对这种情况的建议（来自 [Mixamo 帮助文档](https://helpx.adobe.com/creative-cloud/help/mixamo-rigging-animation.html)）：传**无骨骼** mesh，让 Mixamo 自己 auto-rig。

`scripts/blender/merge_for_mixamo.py` 据此把每个角色的多 FBX 部件 join 成单 mesh + 删光所有 armature → 上传 Mixamo → 拿回带 mixamorig:\* 65 bone 标准骨架的 FBX。

### 关键设计 3：Cast 三人同源策略

最初规划 Tommy（唐艺昕），调研发现 Crazy31139 没 port adult Tommy（只有 Young Tommy 13 岁前传版，骨骼用的还是 Mixamo 而非 ND）。**改用 Tess** —— 同 Crazy31139、同 ND 骨骼、与 Joel 都属 Joel-的-亲密-小队，三人骨架 100% 一致，省两次 retargeting 胶水。

### 关键设计 4：数据分级

- raw archive（~1.5GB，可从 URL 重下）→ `data/round-0/raw/`，gitignored，**仅 INVENTORY.md + .gitignore 入 git**
- intermediate `.blend`（~50-200MB，可从 raw 重生）→ gitignored
- normalized `.fbx`（~28MB，**Mixamo Auto-Rigger 每次 marker 标记略有差异，不严格可重生**）→ git-lfs 入库

### 开发内容概括

| 产物                               | 路径                                                        |
| ---------------------------------- | ----------------------------------------------------------- |
| 需求                               | `docs/0-*/PROMPT.md`（来自 issue #1）                       |
| 计划                               | `docs/0-*/PLAN.md`（含 4 决议表 + 4 风险表 + 工作日志）     |
| 总结                               | `docs/0-*/SUMMARY.md`（本文）                               |
| Headless Blender 检查脚本          | `scripts/blender/inspect_model.py`                          |
| Headless Blender 合并脚本          | `scripts/blender/merge_for_mixamo.py`                       |
| Raw 来源 + license + 重下脚本      | `data/round-0/raw/INVENTORY.md`                             |
| 合并前检查输出                     | `docs/0-*/inspect-output/{joel,ellie,tess}.txt`             |
| 合并后（Mixamo 后）检查输出        | `docs/0-*/inspect-output/post-mixamo/{joel,ellie,tess}.txt` |
| **核心产物** Mixamo retargeted FBX | `data/round-0/normalized/{joel,ellie,tess}.fbx`（git-lfs）  |

### 额外产物（除核心代码外）

- **跨 OS 工作流文档**（PLAN.md 末段「Fallback 路径」）：Plan B/C 触发时的 Windows 双 clone + git 当桥流程，本轮没用到但留作未来参考
- **Mixamo 上传决策树**（PLAN 决议表 + 本文「关键设计 2」）：解释为什么剥骨而非保留 ND 骨骼
- **Cast 映射调研**：演员 ↔ 角色 + 现成模型可用性逐一确认
- **数据分级 + git-lfs 配置模板**（项目根 `.gitattributes` `*.fbx filter=lfs`）：未来轮次的 FBX 产物自动走 LFS
- **`/start` skill 应用示例**：用 issue #1 驱动开 round，PROMPT 顶部 issue 引用区块

## 数据一览

三人最终骨架完全一致：

| 角色  | normalized .fbx 大小 | mesh verts | mesh faces | armature bones | 骨骼命名      |
| ----- | -------------------- | ---------- | ---------- | -------------- | ------------- |
| Joel  | 8.8 MB               | 111063     | 162533     | 65             | `mixamorig:*` |
| Ellie | 7.0 MB               | 80178      | 131434     | 65             | `mixamorig:*` |
| Tess  | 12 MB                | 150279     | 217488     | 65             | `mixamorig:*` |

Ellie 的 verts 比 pre-Mixamo 少 ~3.6k —— Mixamo 内部 weld 了重复顶点，正常。

## 局限性

| 类别         | 现状                                                                                        | 影响                                                                                                                                |
| ------------ | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **面部表情** | 没有 blendshape；Mixamo 不生成；ND 原 face bones 在 merge 阶段一并剥了                      | 三人脸都是僵的，不会眨眼/嘴动；舞蹈视频肉眼可察                                                                                     |
| **贴图**     | normalized FBX mesh-only，材质 = 0；原始 `.dds` 在 `data/round-0/raw/{character}/Textures/` | PROMPT 第三项「贴图正确显示」未在 normalized 上闭环；已拆分为独立 issue [#3](https://github.com/pkulijing/tlou-dance/issues/3) 跟踪 |
| **物理副骨** | hair-cloth / jacket-cloth / strap-cloth 的 sub-rig 全弃                                     | 头发 / 衣服 / 带子不会飘，整体会显得偏「假人」                                                                                      |
| **手指精度** | Mixamo 标准 4 关节 × 5 指 × 2 手 = 40 根；ND 原可能更细                                     | 舞蹈手势 OK，特写镜头会平                                                                                                           |
| **License**  | Crazy31139 fan port，原资产版权归 Naughty Dog / Sony；非商业 fair use 范畴                  | 最终视频要写 Naughty Dog / Sony / Crazy31139 出处声明                                                                               |

## 后续 TODO

按优先级：

1. **Spike #2（issue [#2](https://github.com/pkulijing/tlou-dance/issues/2)）启动**：从《心愿便利贴》视频提取 motion，输出 BVH / SMPL → retarget 到 Mixamo 65 bone 骨架。本 spike 已就绪等用。
2. **Round 1 烟测**（建议）：用 Mixamo 自带某个简单舞蹈动作（如 "Salsa Dancing"）应用到 normalized/joel.fbx，跑通「Mixamo 动作 → Mixamo 骨架 → 我们的 mesh」最短路径，验证管线。失败成本低、信号大。
3. **贴图集成进 normalized FBX**（已开 issue [#3](https://github.com/pkulijing/tlou-dance/issues/3)）：写 `wire_textures_into_normalized.py`，几何匹配 polygon → raw 部件 → 挂 PBR 材质 + .dds 贴图，导出带 embedded textures 的 FBX 覆盖现有 normalized 文件。**spike #1 范围内未做但路径已明** —— 渲染最终视频前必须完成。
4. **面部表情 mocap pipeline**（已开 issue [#4](https://github.com/pkulijing/tlou-dance/issues/4)，P2）：spike 调研后端（Flow Studio Free / DeepMotion / SMPL-X 系列 / FreeMoCap+VIPER）+ 前端给角色加 ARKit 52 blendshape 路径。**依赖 #2 先通**。
5. **物理 sim 还原**（更长期）：Blender Cloth 模拟头发 / 夹克 / 背包带，按需即可。

## 致谢

- 模型 fan port: [Crazy31139](https://www.deviantart.com/crazy31139)（DeviantArt）
- 原始资产: [Naughty Dog](https://www.naughtydog.com/) / Sony Interactive Entertainment（《The Last of Us Part I / Part II Remastered》）
- 自动绑骨: [Mixamo](https://www.mixamo.com/)（Adobe）
