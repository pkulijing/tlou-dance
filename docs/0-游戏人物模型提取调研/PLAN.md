# Round 0 — PLAN.md

## 目标回顾

本轮验证：能否拿到 3 个可用的 TLoU 主角模型（Joel / Ellie / Tess），导入 Blender 后看到 mesh + 骨骼 + 贴图，并统一到 Mixamo 骨骼，让后续 Spike #2 的 motion 数据可一次驱动三人。

**调研已完成**：3 位主角全部有现成 fan port 可下载，**不需要自己从游戏 psarc 解包**，本轮从 2 天压缩到 ~1 天。

## 已确认决议

| 决议项       | 选择                                                                                                                                                                                                                                                                                                                         | 备注                                                                                                                                   |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 提取策略     | **Plan A：下载现成 fan port**                                                                                                                                                                                                                                                                                                | 节省双 OS 切换；自解包 Plan B/C 仅作 fallback                                                                                          |
| 工作环境     | **Linux 主 dev clone**                                                                                                                                                                                                                                                                                                       | Plan A 全程 Linux 即可；进 Windows 仅在 Plan B/C 触发时                                                                                |
| Cast 映射    | Joel ↔ 王濛 / Ellie ↔ 李小冉 / Tess ↔ 唐艺昕                                                                                                                                                                                                                                                                                 | 对应浪姐 7 一公《心愿便利贴》三人组                                                                                                    |
| 模型来源     | Joel: [Crazy31139 TLOU2 Jackson](https://www.deviantart.com/crazy31139/art/TLOU2-Joel-Jackson-854239224) / Ellie: [Crazy31139 TLOU2 Seattle](https://www.deviantart.com/crazy31139/art/TLOU2-Ellie-Seattle-853552008) / Tess: [Crazy31139 TLOU Part 1](https://www.deviantart.com/crazy31139/art/TLOU-Part-1-Tess-956024857) | **三人同源**（Crazy31139）+ 同骨骼系统（ND 原骨骼）+ 同提取风格（fbx + 分离 .dds），最省 retarget 工作量                               |
| 骨骼统一目标 | **Mixamo 骨骼**                                                                                                                                                                                                                                                                                                              | 三个 .fbx retarget 到同一套 rig，让 Spike #2 一份 BVH 驱动三人                                                                         |
| Blender 平台 | **Linux native**                                                                                                                                                                                                                                                                                                             | Blender 跨平台、Linux 一等公民；整条流水线（验证 / retarget / 渲染）都在 Linux 跑；仅 fallback Plan B/C 的 Noesis 解包步骤需要 Windows |

## 阶段拆分

### Phase 0 — 下载 + 落 raw assets（预计 30min）

> 全程 Linux 端本 clone 操作。开分支：`git checkout -b round/0-asset-extract`

- 建目录：`data/round-0/raw/{joel,ellie,tess}/`（重数据放项目根 `data/`，docs 只放文档）
- 按上表 Sources 下三份模型包到对应目录（全部 DeviantArt + Yandex Disk 公开链，走 Yandex Disk API → curl）
- 解压，记录每包实际文件构成（.fbx / .ascii / .smd / .blend / 贴图清单），写到工作日志
- 早期 commit：`git add data/round-0/raw/.gitignore data/round-0/raw/INVENTORY.md && git commit -m "wip(round-0): 落 raw INVENTORY"`（实际 raw archive 全部 gitignored）

### Phase 1 — Blender 验证 + Mixamo 骨骼统一（预计 半天）

每个角色按四步走：

1. **载入 + 三项基础验收**（Blender 打开 .fbx）：
   - 几何：无破洞、UV 正确
   - 骨骼：可见、变换骨骼能带动 mesh
   - 贴图：至少 base color + normal 正确加载
2. **Retarget 到 Mixamo 标准骨骼**：
   - 优先：上传到 [Mixamo](https://www.mixamo.com/) 走 auto-rig（账号免费，输出标准 `mixamorig:*` 命名）
   - 备选：本地用 [Auto-Rig Pro](https://blendermarket.com/products/auto-rig-pro)（付费）/ Blender 内置 Rigify
3. **导出标准化 .fbx**：
   - 落到 `data/round-0/normalized/{joel,ellie,tess}.fbx`
   - 文件名约定：小写英文名，便于后续脚本批量加载
4. **截图存档**：每角色三张 — 正面 / 骨骼线框 / 材质渲染 — 落 `assets/screenshots/{joel,ellie,tess}-{angle}.png`

任一角色质量不达标 → 切对应 Plan B（见 fallback 段），仅该角色走自解包，不要全员重来。

### Phase 2 — 工作日志整理 → SUMMARY.md（预计 半天）

按 Constitution 模板（背景 / 实现方案 / 关键设计 / 局限性 / 后续 TODO）。重点写：

- **可行性结论**：「全员现成可用 + 已统一骨骼，Spike #1 通过」/ 部分通过 / 不通过
- **三个模型来源 + license / fair use 说明**（玩具项目非商业；最终视频发布时注明 Naughty Dog/Sony 出处）
- **Mixamo retarget 工作流**：精确步骤 + Blender 版本，方便后续复用
- **遗留问题**：例如某模型贴图缺 normal、Tess 手指骨简化、Mixamo 自动绑骨在腋下/裙摆区的常见失配

## 风险与 Stop conditions

| 风险                                              | 应对                                                                                                                                 |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| R1：现成模型质量差（破面 / 骨骼缺失 / 贴图缺失）  | 切该角色对应 Plan B（自解包），其他角色继续 Plan A                                                                                   |
| R2：Mixamo auto-rig 在手指 / 表情上失配           | 接受简化：只对身体大关节 retarget，手指/表情留空（spike 不追求精度，舞蹈主要是身体动作）                                             |
| R3：单角色 .fbx + 贴图 > 50MB 触发 git 大文件警告 | 评估启用 git-lfs；或先 commit 精简版（low-poly LOD + 主贴图）                                                                        |
| R4：fan port 是 .ascii / .smd 等非标准格式        | 用 [XPS Tools (XNALaraMesh)](https://github.com/johnzero7/XNALaraMesh) Blender 插件转换                                              |
| R5（已消解）：三人骨骼一致性                      | 切到 Crazy31139 Ellie (Seattle) 后三人同 ND 原骨骼，retarget 步骤可批量套用同一映射；初期 Open3DLab 那份 Rigify+Faceit 的 Ellie 已弃 |

**Stop conditions**：

- 1 天硬上限到 → 不论是否跑通都写 SUMMARY 给阶段性结论
- 三个角色全失败 → 切 final fallback：用 Mixamo 自带 mannequin（统一骨骼天生满足），Spike #1 标记「不可行 / 用 mannequin 替代」，Spike #2 仍可启动

## Fallback 路径（仅 Plan A 某角色失败时启动）

**Plan B：从本地 Part I 安装自解包**

进 Windows，回到本 PLAN 的「跨 OS 工作流」走双 clone（见末尾备份段）：

- [ndarc](https://www.nexusmods.com/thelastofuspart2/mods/31) 解 `sp-common.psarc` → `.pak` 文件
- [fmt_nd_pak](https://github.com/alphazolam/fmt_nd_pak) Noesis 插件载入 → 选目标角色 → 导出 .fbx
- 拿到 .fbx 后回到 Linux 端 Phase 1 第 2 步（retarget）

**Plan C：Part II Remastered 同链路（最完整资产）**

同 Plan B，区别：

- 装 [TLOU2R Vortex 扩展](https://www.nexusmods.com/site/mods/1250) 自动配置 ndarc + ndmodloader
- 用 [Speclizer's Actor Browser](https://www.nexusmods.com/thelastofuspart2/mods/26) 找角色资产路径
- 之后同 Plan B 的 Noesis + fmt_nd_pak 导 .fbx

**跨 OS 工作流（仅 Plan B/C 启动）**

- Windows 端：`git clone git@github.com:pkulijing/tlou-dance.git D:\dev\tlou-dance`，checkout `round/0-asset-extract`
- 自解包结果落 `data/round-0/raw/{character}-from-game/`，commit + push
- Linux 端 `git pull` 后续 retarget；最终 SUMMARY 写在 Linux 端

## TDD 适用性

按 Constitution「探索性原型、与外部系统的集成」例外条款，本轮**不强制 TDD**。关键产出是模型文件 + Blender 肉眼验证 + 一份 Mixamo 工作流文档。Spike #2 的 BVH retarget pipeline 涉及代码契约时再走 TDD。

## 工作日志

（开发过程中边做边记，最后合入 SUMMARY.md）

### Phase 0（已完成）

- 建分支 `round/0-asset-extract`，起 `assets/{raw,normalized,screenshots}/` 目录树
- 下载三人 raw 包，**全走 Yandex Disk public API**（curl + python3 解 JSON href）；详见 `data/round-0/raw/INVENTORY.md`
- 中途切换 Ellie 来源：Open3DLab FrankDP1 (Rigify + FaceitRig，骨骼不匹配 + 78/79 贴图死链 + 疑似 young Ellie) → Crazy31139 TLOU2 Seattle（ND 原骨骼，与 Joel/Tess 同源）
- 写 `scripts/blender/inspect_model.py`（headless Blender，CLI: `blender --background --python ... -- file1 [file2 ...]`），跑出三人 inspect-output：
  - **Joel**：7 个 FBX 部件，ND 原骨骼 1548 bones，~111k verts；7 个重复 armature（Phase 1 需清理）
  - **Ellie (Seattle)**：12 个 FBX 部件，ND 原骨骼 1845 bones，~84k verts（采样 6/12 部件）；6 个 armature（含 hair/jacket 物理 sub-rig）
  - **Tess**：1 个合并 FBX (`tess.mesh.fbx`)，ND 原骨骼 1918 bones，~150k verts；1 个 armature ✨ 最干净
- raw archive 总计 ~1.5GB，加 `.gitignore` 不入 git
- **Phase 1 待办**：(a) 三人合并 + 清理 multi-armature；(b) 从 `Textures/*.dds` 自动 wire 材质（推荐写脚本）；(c) Blender GUI 验证三项验收（mesh / 骨骼 / 贴图）；(d) 上 Mixamo retarget；(e) 导 normalized FBX

### Phase 1（待开始）

- ……
