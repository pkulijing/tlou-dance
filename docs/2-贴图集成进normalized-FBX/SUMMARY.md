# SUMMARY — 贴图集成进 normalized FBX（spike 失败）

> 关联 issue：[#3 贴图集成进 normalized FBX (Joel/Ellie/Tess)](https://github.com/pkulijing/tlou-dance/issues/3)
>
> **结论**：本轮作为 spike 视为失败 —— 没能交付一份"导入 Blender 即看到带正常贴图角色"的 FBX。但**根因被定位、新发现固化、约 80% 的代码（pure-logic 模块 + 41 个单元测试）可在根因解决后立即复用**。

## 1. 开发项背景

希望解决的问题：

round 0 spike #1 交付的三人 normalized FBX（Joel/Ellie/Tess）`mesh + Mixamo 65-bone 骨架`完整，但材质槽空、无贴图引用 —— Blender 打开是灰人。raw .dds 贴图（每人 200+ 张）已下载并按部件分目录摆好，本轮把贴图挂上让 normalized FBX 真正"直接可用"。

预设交付：脚本 + 一次成功 dry-run（三张 Blender viewport 截图证明带贴图正常显示），FBX 本身 gitignored 不入库。

## 2. 实现方案

### 关键设计

**统一三人的"带标签参考点云 + KD-tree match"算法**：

- raw 部件 mesh 的所有 polygon 中心 + 部件标签 → 参考点云
  - Joel/Ellie：标签 = 多 FBX 文件名 stem
  - Tess：标签 = 单 FBX 内 27 个 submesh 的 object 名前缀经别名表映射
- normalized 的 joined mesh 每个 polygon 中心 → KD-tree 找最近 ref → 分配部件标签
- 按部件名给 normalized mesh 加 material slot，连接 PBR 贴图，导出 FBX with embed_textures

KD-tree 实现：numpy chunked brute-force（避开 scipy 依赖在 Blender 自带 Python 里装不上）。

**spike 期间的多个有效新发现**（详见 [PLAN.md](PLAN.md) §1 与下文「额外产物」）：

1. **Tess 不是退化情况**：原 PROMPT 假设 Tess 单 mesh 无法精细贴图，实地侦察发现 `tess.mesh.fbx` 内含 27 个独立 object（眼球/睫毛/牙齿/唾液都是独立 mesh，比 Joel/Ellie 还细分）—— 算法在三人间统一，无需 Tess 特殊路径
2. **cloth-sim 附件无独立贴图**：游戏引擎 cloth helper 共享父部件材质，Joel `joel-backpack-strap-cloth` / Ellie `ellie-jacket-cloth` 等需归并到对应主部件
3. **子文件夹名 ≠ 内部文件前缀**：Joel `Textures/joel-pants/` 实际全是 `joel-new-pants-*` 文件；`Textures/joel-body/` 全是 `joel-arms-*`。游戏的"美术工作流前缀"不等于"mesh 导出部件名"。`detect_dominant_part_prefix` 自动按"覆盖核心通道数最多"投票选主前缀解决了 Joel/Ellie 全部 11 处 mismatch
4. **TLOU 的 DDS 子格式 Blender 4.5 不解** ← **根因失败点**

### 开发内容概括

`scripts/texture_wiring/`（pure-logic，可被 Blender 与 pytest 共用）

- `texture_parser.py`：扫 part_dir 找 PBR 4 通道，过滤 `_TEST` / hex hash / 跨 part 共享贴图，多副本 `(N)` 取最早；含 `detect_dominant_part_prefix`
- `part_assigner.py`：numpy chunked brute-force 最近邻匹配
- `alias.py`：Tess submesh 名前缀 → 贴图前缀映射 + cloth-sim 附件 → 父部件继承

`scripts/blender/wire_textures_into_normalized.py`：Blender headless entrypoint，串起 import / KD-tree match / 建材质 / export FBX。

`tests/`：41 个单元测试覆盖三个 pure-logic 模块（parser 16 / assigner 8 / alias 17），全绿，跑 `uv run pytest tests/` 确认。

### 额外产物

- `pyproject.toml` 加 numpy 到 dev deps；加 `[tool.pytest.ini_options] pythonpath = ["scripts"]` 让脚本模块可被测试 import
- `tests/conftest.py` 提供 `fixtures_root` fixture（虽然实际测试都用 `tmp_path` 运行时构造）
- `data/round-2/normalized/joel.fbx`（8.6MB，本地 dry-run 残留，gitignored）—— 仅 mesh + Mixamo 骨架，5 material slot 但贴图都没成功嵌入

## 3. 局限性（spike 失败的根因）

### 核心：Blender 4.5 解码 TLOU 的 DDS 失败

TLOU 的 DDS 文件用了 Blender 4.5 内置图像解码器**不支持的子格式**（很可能是 BC5 / BC7 / DX10 ATI2 等带压缩的法线/RGB 变体）。表现：

| 路径                                  | 失败方式                                                                                                                                       |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `bpy.data.images.load(dds)` 直接 load | `has_data = False`（懒解码或不解）                                                                                                             |
| 试图 `image.save()` 转 PNG            | `RuntimeError: Image does not have any image data`                                                                                             |
| FBX export with `embed_textures=True` | DDS 二进制被作为 blob 嵌入（FBX 体积是对的），但 Blender 重 import 时同样的解码器失败 → viewport 看到 **roughness=0 镀铬** 或 **color=黑全灰** |

简单 shader 图（直连 BSDF）能让 FBX 携带 17 张贴图（vs 复杂图只剩 2 张），但带过去也解不出，等于白搭。

### 衍生：本地 dry-run 截图缺失

由于 viewport 解码不出，三人 viewport 都做不到「带正常贴图」效果，原计划三张截图作交付证据没拿到（截图只能是镀铬版或全灰版，反而误导）。

### Tess 与 Ellie 实际未跑

Joel 跑了多次但都卡在解码问题上，Ellie / Tess 没必要再各自跑一遍 —— 同一根因，结果可预期。代码本身能跑（pure-logic 全绿测试），跑出来 FBX 也是同样的解码废样。

## 4. 后续 TODO

按优先级：

1. **解决 DDS 解码**（解决了上面所有问题就解决了）。可选路径：
   - 装 ImageMagick 或 Microsoft texconv，DDS → PNG 离线预处理（外部命令脚本，不进 Blender）
   - 用 Python 的 `imageio` 或 `Pillow + dds-pillow-plugin` 在 uv 环境里离线转，避开 Blender 的解码器
   - 探索 Blender 4.6+ 是否改进了 DDS 支持
2. **跑通预转换后**，重做 Ellie / Tess 的端到端，补三张 viewport 截图
3. **法线极性 G 翻转**：DDS 转 PNG 时同步把 G 通道 1-x，烘进 PNG，解决 DX→OpenGL 凸凹反向问题（PLAN §2.4 原计划）
4. **AO 通道**：DDS 转 PNG 时把 AO 乘到 color 上烘出新 color PNG，恢复立体感（PLAN §2.3 原计划）
5. **Joel `joel-body` 主贴图选择**：当前 auto-detect 给出 `joel-inside-shirt`，但 viewport 没看到无法判断对错。等贴图能解码了再校验
6. **`add_leaf_bones=False` 参数验证**：当前导出 FBX armature 默认行为，未确认 leaf bones 是否影响 Round 3+ mocap retarget

## 5. 经验教训（给未来挑同类 spike 的人）

- **早期跑一次"端到端 dry-run"**：本轮如果在 Phase A/B（写测试 + 实现 pure-logic）之前先做 30 分钟 spike `bpy.data.images.load(some_dds.dds); print(img.has_data)`，会立刻发现解码问题，可以在写脚本框架前就决定是否要走外部解码工具路径。**不要把数据格式假设藏到 Phase C 才暴雷**
- **测试用 `tmp_path` + 空 `.dds` 文件**对验证 parser 字面匹配/过滤逻辑是足够的，但**完全不验证图像数据本身能否被 Blender 用**。本轮 41 个测试全绿但仍然 spike 失败，就是因为测试只盖到了 pure-logic 层，没盖到 bpy 集成层（Constitution 也允许集成层先跑通再补烟测，但"先跑通"这步本身的价值就在这种地方体现）
- **Issue 自评 P1（spike #2 + Round 1 烟测可用灰模，渲染前必须解决）现在仍成立** —— 本轮没把灰模换掉，下游 Round 3+ 仍可用现有灰模继续。所以本轮失败不阻塞主线，只是把"贴图集成"这件事推后到知道怎么解 DDS 之后
