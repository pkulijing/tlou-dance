> 来自 [#3 贴图集成进 normalized FBX (Joel/Ellie/Tess)](https://github.com/pkulijing/tlou-dance/issues/3)
> Labels: `type:feat` `area:asset-extract` `priority:P1`

## 背景

round 0 spike #1 以"feasibility 验证 + 灰模交付"收尾。三人 normalized FBX 现在 mesh + Mixamo 65-bone 骨架齐，但材质槽空、无贴图引用 —— Blender 打开是灰人。原始 .dds 贴图（每人 200+ 张）已下载、按部件分目录摆好在 `data/round-0/raw/<character>/TLOU* - <Character>*/Textures/<part>/`。本任务把贴图挂上让 normalized FBX 真正"直接可用"。

### 前置澄清：贴图与动作的时序关系

`/start` 时 CC 与作者澄清：动作（armature 上的 mocap 关键帧）与贴图（mesh 上的 PBR 材质）在 Blender 里是**独立两层**，通过 mesh 的 skin modifier 关联但互不依赖。因此 #3 不阻塞 #2（Round 1 动捕 spike，作者另一 worktree 并行）和 Round 3+（用 mocap 驱动灰模真正跳起来）—— 只需要在**最终整活视频渲染输出前**把贴图挂上即可。本轮纯本地后处理。

这也解释了 issue 自己的优先级判定："P1 而非 P0"：因为下游不阻塞，但成片不能是灰人。

## 希望达到

**交付物 = 能力（脚本）+ 一次成功 dry-run 证据**，不 commit 生成的 FBX 本身。具体：

1. **脚本** `scripts/blender/wire_textures_into_normalized.py` —— 纯函数 `(灰模, raw 贴图) → 带贴图 FBX`，可重跑
2. **本地一次成功跑通** —— 输出 `data/round-2/normalized/{joel,ellie,tess}.fbx`（**gitignored**，本地保留），导入 Blender 切 `Material Preview` 视图能看到带贴图的角色
3. **dry-run 证据** —— 三人各一张 Blender viewport 截图存到 SUMMARY.md，证明脚本端到端跑通

### 为什么不 commit FBX 本身

带贴图 FBX 是**生成产物**而非源：脚本 + raw 贴图 + 灰模三个输入都已就绪（前两个有 INVENTORY 或本地 raw，灰模 commit 了），任何时候本地能重生成。下游 Round 3+（mocap retarget）只用灰模就够（材质不参与运算），唯一需要带贴图的是**最终成片渲染那一次**，到时本地重跑脚本即可。

参考策略 A（详见 `/start` 对话纪要）：避免 ~250MB LFS 配额浪费在一次性产物上。

## 产物管理

- `data/round-2/normalized/.gitignore` —— ignore `*.fbx`，但 commit `.gitignore` 本身和 `INVENTORY.md`
- `data/round-2/normalized/INVENTORY.md` —— 一句话说明"运行 `scripts/blender/wire_textures_into_normalized.py` 重生成"

## 候选方向

### 方向 A（推荐）：纯本地后处理脚本 `scripts/blender/wire_textures_into_normalized.py`

**不动 Mixamo**，全程在本地 Blender headless 跑：

1. 读现有 normalized FBX（已 joined mesh + Mixamo 骨架）
2. 同时 import 7 个 raw 部件 FBX 作几何参考（每部件先建对应 PBR 材质）
3. 对 joined mesh 每个 polygon 算中心坐标，用 KD-tree 找最近的 raw 部件 polygon → 确定面所属部件
4. 给 joined mesh 加多个 material slot，按归属设 `polygon.material_index`
5. 每个 material 从 `Textures/<part>/` 自动挂 .dds（沿用 round 0 早期 wire_textures.py demo 留下的 glob/过滤逻辑：`*-color`/`*-normal`/`*-roughness`/`*-ao`/`*-mask` 命名约定）
6. 导出 FBX with `embed_textures=True` 到 `data/round-2/normalized/{character}.fbx`（gitignored，本地保留作 dry-run 验证）

### 方向 B：改 `merge_for_mixamo.py` 在 join 前赋材质，重传 Mixamo

需要手动重做 Mixamo marker 操作，**不推荐**（破坏 round 0 的产物可重现性、且要重过一遍 web GUI）。

## 风险 / 注意点

- **几何匹配鲁棒性**：Mixamo 内部对 Ellie weld 了 ~3.6k 顶点（round 0 已观察），polygon center 应仍稳定，KD-tree 距离阈值容错。最坏情况切方向 B
- **DDS 格式**：Blender 原生支持；命名约定（`*-color/*-normal/*-roughness/*-ao/*-mask`）已在 raw 里观察过
- **生成产物体积**：本地估算 ~80-100MB/人，三人合计 ~250MB；因 gitignored 不影响仓库

## 范围预估

1-2h 主路径；几何匹配若不鲁棒留 3-4h 兜底。

## 关联

- 依赖 #1 (round 0) 的产物 `data/round-0/normalized/*.fbx` 和 `data/round-0/raw/`
- 与 #2（动捕 spike，作者另一 worktree 并行）无依赖关系
