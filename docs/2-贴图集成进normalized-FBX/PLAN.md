# PLAN — 贴图集成进 normalized FBX

## 0. 关于本计划

本轮交付物 = **脚本** + **三人各一张 Blender viewport 截图证据**，FBX 本身 gitignored 不入库（详见 [PROMPT.md](PROMPT.md) 的"产物管理"段）。

本计划遵循全局 Constitution 的 TDD 约束：纯逻辑部分**先写失败单测、再写最小实现**；Blender 集成层（bpy 调用）作为"与外部系统集成"例外，**先跑通再补烟测**。

## 1. 实地侦察结论（固化）

### 1.1 各角色 raw 资产结构

| 角色  | 部件来源                       | 部件数 | 标签来源                                           |
| ----- | ------------------------------ | ------ | -------------------------------------------------- |
| Joel  | 7 个独立 FBX 文件              | 7      | FBX 文件名（如 `joel-body.fbx` → `joel-body`）     |
| Ellie | 14 个独立 FBX 文件             | 14     | FBX 文件名                                         |
| Tess  | **1 个 FBX 内含 27 个 object** | 27     | object 名前缀（如 `head_tess_head_01_*` → `head`） |

### 1.2 贴图目录布局

| 角色  | Textures/ 结构                       | 命名                                                       |
| ----- | ------------------------------------ | ---------------------------------------------------------- |
| Joel  | 6 个子文件夹（按部件）               | `<part>-<channel>.tga(N).dds`                              |
| Ellie | 11 个子文件夹 + 大量共享贴图平铺在根 | `<part>-<channel>.tga(N).dds`                              |
| Tess  | 完全平铺（无子文件夹），~180 个 DDS  | `tess-<part>-<channel>.dds` 或 `tess_<part>_<channel>.dds` |

### 1.3 资产"残缺"实情

不是真残缺。**主体部分（脸/身/裤/发/包）三人都全**。"缺"的只是 cloth-sim 附件（`*-cloth.fbx`）—— 这些是引擎里只有 mesh 没有独立贴图的飘动布料，**继承父部件材质**即可：

| 角色  | 无独立贴图的 cloth 附件                                                            | 继承自                       |
| ----- | ---------------------------------------------------------------------------------- | ---------------------------- |
| Joel  | `backpack-strap-cloth`                                                             | `joel-backpack`              |
| Ellie | `bandage-forearm-cloth`, `backpack-zip-cloth`, `jacket-cloth`, `strand-hair-cloth` | 同名父部件去掉 `-cloth` 后缀 |

### 1.4 噪声过滤

DDS 文件夹里大量噪声需排除：

- `_TEST.dds` / `_TEST*.dds`：调试残留
- `<16 位 hex>_dx10.dds`：模型工具 dump 副产物
- 跨角色泄露贴图（Joel 的 head 文件夹里有 `dina-*` / `ellie-*`）
- 全局共享贴图（`blood-*`, `default-*`, `fabrics-*`, `mask*-*`, `mud-*`, `snow-*`, `goop*` 等）

→ **过滤规则**：只挑 `<part-name>-{color,normal,roughness,ao}*.dds` 的精确匹配。

## 2. 设计：脚本架构

### 2.1 模块划分

```
scripts/
├── blender/
│   └── wire_textures_into_normalized.py   ← Blender entrypoint，import bpy
└── texture_wiring/                         ← 纯逻辑模块，无 bpy
    ├── __init__.py
    ├── texture_parser.py                   ← 扫 Textures/ 找 part→{color, normal, roughness, ao} 路径
    ├── part_assigner.py                    ← KD-tree polygon 中心 → 最近 part 标签
    └── alias.py                            ← Tess mesh 名前缀 → 贴图前缀映射 + cloth 父部件继承规则
```

`tests/` 对应 `texture_wiring/` 同名 `test_*.py`。

### 2.2 数据流

```
[Blender entrypoint]
  1. import normalized FBX → joined mesh M, armature A
  2. import raw 部件 mesh（Joel/Ellie 多 FBX 或 Tess 单 FBX）
  3. 为每个 raw 部件 mesh 算 polygon 中心数组 + 标签数组 (part_name)
  4. 对 (centers, labels) 调 part_assigner → 给 M 每个 polygon 分配 part 标签
  5. 调 texture_parser 为每个 part 找贴图文件路径
  6. 调 alias 处理 Tess 别名 + cloth 继承
  7. 在 M 上建 material slot，每 slot 一个 Principled BSDF（Color + Normal + Roughness + AO 全通道）
  8. 设 polygon.material_index
  9. export FBX with embed_textures=True 到 data/round-2/normalized/<character>.fbx
```

### 2.3 PBR 通道范围（决策）

**全 4 通道：Color + Normal + Roughness + AO**。文件都已下载在每部件 Textures/ 子文件夹下，parser 一次扫四种 suffix、Blender shader 一次连 4 个 socket 即可。不全做反而要为"省 10-15 分钟"破坏 PBR 质量、产生塑料感。

**通道缺失策略**：parser 找不到某 channel 时返回 None，Blender 层对应 socket 不连（Principled BSDF 用默认值），不阻塞流程。

### 2.4 Normal map 极性处理（DirectX → OpenGL）

TLOU 是 PS/DirectX 平台游戏，原始 normal map 大概率按 **DirectX 约定**（Y 朝下）。Blender 默认按 **OpenGL** 约定（Y 朝上）解读，**直接挂上会出现"凹凸反向"**：眉骨变凹陷、脸颊褶皱倒过来、整张脸像吹气球 ——视觉上一眼"不对劲"但说不出哪里。

**默认就修**：在 normal map 节点链里加 G 通道反转：

```
Image Texture (Non-Color) → Separate Color (RGB)
                          → R 直连 / B 直连 / G → Math (Subtract from 1.0) → Combine Color
                          → Normal Map node → Principled BSDF.Normal
```

如果某角色截图反而看着不对（说明那个特定贴图是 OpenGL 约定），临时去掉反转节点重跑 —— 但默认仍按 DX 处理。

镜像 UV 问题（左右脸 tangent space 错乱）保留为 BACKLOG，截图发现"半边脸不对"再开新 issue。

## 3. TDD 测试用例清单

### 3.1 `texture_parser.parse_part_textures(part_dir: Path) -> dict[str, Path]`

输入：`Textures/<part>/` 目录路径
输出：`{"color": Path, "normal": Path, "roughness": Path | None, "ao": Path | None}`，未匹配的 channel 为 None

| 用例                                                                              | 输入 fixture                                                                                                                | 期望输出                                |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **正常**：四通道齐全                                                              | 含 `joel-body-color.tga(1).dds`, `joel-body-normal.tga(1).dds`, `joel-body-roughness.tga(1).dds`, `joel-body-ao.tga(1).dds` | 4 个 channel 都映射上                   |
| **缺通道**：仅 color + normal                                                     | 只有前两个                                                                                                                  | color、normal 映射，roughness/ao = None |
| **过滤 \_TEST**：有 `*_TEST.dds`                                                  | 含 `joel-body-normal.tga(1)_TEST.dds`                                                                                       | `_TEST` 文件被忽略                      |
| **过滤 hex hash**：有 `<16hex>_dx10.dds`                                          | 含 `725E5BD2572EE050_dx10.dds`                                                                                              | hash 文件被忽略                         |
| **过滤共享**：有 `blood-color.tga(1).dds`                                         | part_dir=`joel-body` 但目录里有 blood/default/fabrics 等                                                                    | 跨 part 文件被忽略                      |
| **多副本去重**：`joel-body-color.tga(1).dds` 和 `joel-body-color.tga(2).dds` 都在 | 选 `(1)` 那个（最早下载的）                                                                                                 |

### 3.2 `part_assigner.assign_polygons(query_centers, ref_centers, ref_labels) -> list[str]`

输入：query 多边形中心数组 (N×3)，ref 多边形中心数组 (M×3)，ref 标签数组 (M)
输出：query 每个多边形对应的 part 标签 (N)

| 用例                           | 输入                                                                             | 期望输出                                                              |
| ------------------------------ | -------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **正常**：两簇分明             | query=[(0,0,0), (10,10,10)], ref={(0,0,0): "head", (10,10,10): "body"}           | `["head", "body"]`                                                    |
| **多簇**：3 query 落 3 cluster | query=[(0,0,0), (5,0,0), (10,0,0)], ref={"a"@(0,0,0), "b"@(5,0,0), "c"@(10,0,0)} | `["a", "b", "c"]`                                                     |
| **等距**：query 在两 ref 中点  | query=[(2.5,0,0)], ref={"a"@(0,0,0), "b"@(5,0,0)}                                | 任一确定（通常按 KD-tree 实现的 tie-break，**测试中用偏置避免歧义**） |
| **空 query**                   | query=[], ref=非空                                                               | `[]`                                                                  |
| **错位 ref**（debug 用例）     | ref 标签数与中心数不匹配                                                         | 抛 ValueError                                                         |

### 3.3 `alias.tess_mesh_to_part_prefix(mesh_name: str) -> str | None`

| 输入 mesh 名                                                    | 期望部件前缀                                 |
| --------------------------------------------------------------- | -------------------------------------------- |
| `head_tess_head_01_u1_g1_LODShape0_shader2_merged_partition0`   | `tess-head`                                  |
| `pants_tess_pnt_01_u1_g1_LODShape0_shader1_merged_partition0`   | `tess_pants_`                                |
| `shirt_tess_shirt_01_u1_g1_LODShape0_shader0_merged_partition0` | `tess_shirt_`                                |
| `backpack_tess_bkpk_01_*`                                       | `tess-bkpk-`                                 |
| `boots_tess_boot_01_*`                                          | `tess-boot-`                                 |
| `hair_tess_hair_01_*`                                           | `tess_hair_`                                 |
| `scarf_tess_hair_01_*`                                          | `tess-scarf-`                                |
| `eyeballs_tess_head_01_*`                                       | `tess-eyes-`                                 |
| `unknown_xyz`                                                   | `None`（fallback；调用方决定是否报错或归并） |

### 3.4 `alias.resolve_cloth_parent(part_name: str) -> str | None`

| 输入                        | 期望                                                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `joel-backpack-strap-cloth` | `joel-backpack`                                                                                                     |
| `ellie-jacket-cloth`        | `ellie-jacket`（注意：Ellie 没有 `ellie-jacket` 部件，应再回退到 `ellie-body` —— **这条用例测的就是 fallback 链**） |
| `ellie-strand-hair-cloth`   | `ellie-hair` 或 `ellie-hair-cloth`（看实际是哪个 mapped）                                                           |
| `joel-body`                 | `None`（不是 cloth）                                                                                                |

> 注：cloth 继承的 fallback 链需要根据实际 part 名表硬编码，写测试时同步定义。

## 4. 执行步骤

### Phase A：测试基础设施（~15 min）

- [A1] `mkdir tests`，加 `tests/__init__.py`、`tests/conftest.py`（fixtures 目录指引）
- [A2] 准备 `tests/fixtures/textures_joel_body/` 含 4 个 channel 的 fake DDS（用空 `.dds` 文件即可，parser 不读内容）
- [A3] 跑 `uv run pytest tests/` 验证空跑通过

### Phase B：纯逻辑模块 TDD（~45 min）

- [B1] 红：写 `tests/test_texture_parser.py`（6 用例），运行确认全部失败
- [B2] 绿：实现 `scripts/texture_wiring/texture_parser.py`，跑测试至全绿
- [B3] 红：写 `tests/test_part_assigner.py`（5 用例）
- [B4] 绿：实现 `scripts/texture_wiring/part_assigner.py`（用 `scipy.spatial.cKDTree` 或自写 numpy O(NM) brute force）
- [B5] 红：写 `tests/test_alias.py`（13 用例：8 mesh 别名 + 4 cloth 继承 + 1 unknown）
- [B6] 绿：实现 `scripts/texture_wiring/alias.py`

### Phase C：Blender 集成（~75 min）

- [C1] 写 `scripts/blender/wire_textures_into_normalized.py`，调用 Phase B 模块
- [C2] 命令行参数：`--character {joel,ellie,tess}`，`--out-dir data/round-2/normalized/`
- [C3] Shader 节点构造辅助函数 `build_pbr_material(name, color_path, normal_path, roughness_path, ao_path)`：4 通道一次连完，含 §2.4 的 G 通道反转节点链
- [C4] **Joel 先跑通**：`blender --background --python ... -- --character joel`，看输出 FBX 体积、Blender 报错
- [C5] **手工验证**：Blender GUI 打开 `data/round-2/normalized/joel.fbx`，切 Material Preview 视图，**特别检查脸部凸凹方向是否正常**（眉骨突出、不是凹陷），截图存 `docs/2-贴图集成进normalized-FBX/assets/joel-textured.png`
- [C6] Ellie 跑通 + 截图
- [C7] Tess 跑通 + 截图（最复杂；如别名映射有缺漏，加 unknown 警告但不阻塞）

### Phase D：产物管理 + 收尾（~15 min）

- [D1] 建 `data/round-2/normalized/.gitignore`（ignore `*.fbx`，但保留 `.gitignore` 自身和 `INVENTORY.md`）
- [D2] 建 `data/round-2/normalized/INVENTORY.md`：一句话说明"运行 `scripts/blender/wire_textures_into_normalized.py --character <name>` 重生成"
- [D3] 写 `docs/2-贴图集成进normalized-FBX/SUMMARY.md`，含三张截图

总计：~2.75h（B+C 各加 ~15 min 因 PBR 4 通道 + 法线极性处理）。

## 5. 验收标准

1. **测试**：`uv run pytest tests/` 全绿（24 个用例左右）
2. **lint**：`uv run ruff check . && uv run ruff format --check .` 通过
3. **三人脚本跑通**：三个 `blender --background --python ... -- --character <name>` 均**无 traceback** 退出
4. **三张截图**：`docs/2-贴图集成进normalized-FBX/assets/{joel,ellie,tess}-textured.png` 在 Blender Material Preview 视图下能看到角色：
   - **脸**是肉色、**衣服**是布色、**不是灰人**
   - **凸凹方向正常**（眉骨/鼻梁突出、眼窝凹陷；不是反向）
   - **质感分明**（皮肤哑光、眼球高光、衣服布料感 —— 体现 Roughness 正确）
5. **本地三个 FBX**：`data/round-2/normalized/{joel,ellie,tess}.fbx` 存在，每个 50-100MB 量级（gitignored，本地保留作 dry-run 证据）

## 6. 风险与回退

| 风险                                                            | 触发条件                                               | 回退                                                                 |
| --------------------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------- |
| KD-tree 误判（Mixamo weld 后某个 polygon 中心漂出该 part 区域） | 截图能看出局部贴图错乱（如裤子上一小块用了 head 贴图） | 加距离阈值，超阈值的 polygon 标记为 fallback "body" 部件             |
| Tess 别名映射有缺漏（某 mesh 前缀没在表里）                     | 脚本 warn 后用 fallback "head" 兜底                    | 看截图哪里贴图错，补别名表，重跑                                     |
| FBX 体积爆炸（>200MB/人）                                       | embed_textures 后单文件过大                            | 降级 channel 数（去掉 roughness/ao），或将贴图 resize 到 1024        |
| Blender 4.5 导出 embed_textures 与 DDS 不兼容                   | 导出报错                                               | DDS → PNG 转换中间步骤（Blender 内 image.save_render）               |
| Tess raw 内 27 mesh 跨度太大 → KD-tree 无法精确分配             | 看截图                                                 | 切方向 B：在 raw FBX 上预先 join 同 part 前缀的 mesh，作为单一参考簇 |

## 7. 不在本轮范围

- 镜像 UV 问题（左右脸 tangent space 错乱，"半边脸不对"）—— 截图发现再开新 issue
- 用 GUI 自动渲染一帧静态图作为额外证据（截图够用）
- 提升 Tess 不同 sub-mesh（眼球/睫毛/牙齿）的精细贴图效果 —— 主体过得去就行
- 共享 / 全局贴图（`blood-*`, `mud-*`, `snow-*` 等装饰性 decal）的应用 —— 只做基础 PBR
