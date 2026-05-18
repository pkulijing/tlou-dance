# PLAN — 1-动作捕捉调研

> 关联 PROMPT：[PROMPT.md](./PROMPT.md) · 对应 issue [#2](https://github.com/pkulijing/tlou-dance/issues/2)
> Worktree：`/home/jing/Developer/tlou-dance/.claude/worktrees/round-1-motion-extract` · 分支 `round/1-motion-extract`

## 0. 背景与路线决策（关键 — 对齐结论）

PROMPT.md 默认走主流 mocap 仓库（4D-Humans / WHAM / SMPLer-X）的 conda + `setup.py develop` 老路。本项目按 Constitution 一律走 uv，**所有依赖装载用 `uv add` / `pyproject.toml + uv sync`，绝不写 pip**。

用户提了关键反问："**为什么不只拿模型权重、用通用 pytorch 推理跑？基于 modelscope。**" 这一节给出实地核实后的最终结论。

### 0.1 mocap 链路结构（为什么"只用模型不用算法 repo"在本领域不可行）

mocap 不是单一 classifier。视频 → 可驱动 humanoid rig 的动作序列，需要一条**多组件链**：

| 阶段 | 典型实现 | 是否仅"模型权重"？ |
| --- | --- | --- |
| 人物检测 | YOLOv8 / ViTDet | ✅ 权重独立 |
| 多人跟踪 + 切镜身份维持 | PHALP（~3000 行 py + 优化求解） | ❌ 是算法，不是单一模型 |
| 单帧 SMPL 回归 | HMR2.0 / SMPLer-X / WHAM-Net | ⚠️ 权重独立但前后处理散在 repo 多个 py 文件里 |
| SMPL 解码 | SMPL-X 官方 PyTorch 实现 | ✅ 是参数化模型，独立可用 |
| 时序平滑 + 世界坐标对齐 | per-method 不同 | ❌ 是算法 |
| SMPL → BVH/FBX | 开源转换脚本 | ✅ 独立 |

**"只拿模型权重"** 在 ✅ 项可行，但在 ❌ 项必须复用别人的工程代码——否则 = 论文复现，2 天 spike 写不完。

### 0.2 ModelScope 现成 pipeline 是否能短路 — 实地核实结果

读过 modelscope 主仓 3 个最对路 pipeline 的源码：

| Pipeline (model id) | 输入 | 输出 | 多人 | 适合"视频→SMPL+多人+切镜"？ |
| --- | --- | --- | --- | --- |
| `damo/cv_hdformer_body-3d-keypoints_video` | 视频 ✅ | 3D keypoints xyz（**非** SMPL 参数） | ❌ 源码硬编码取首人 | ⚠️ 半残 |
| `damo/cv_hrnet_image-human-reconstruction` | 单张图 ❌ | mesh obj | ❌ | ❌ |
| `human3d-animation` | SMPL+mesh→GLB | 是 motion **synthesis** | — | ❌ 方向反了 |

**结论：ModelScope 上没有任何 pipeline 端到端覆盖本场景需求**。这条路撞不通——不是"还要再尝试一下"，是事实已确认。

### 0.3 收敛后的唯一可行路线

走 4D-Humans 的 `hmr2` 模块当 library 用，配合 PHALP（独立 git repo）做跨切镜跟踪：

```
源视频 (~/Downloads/xinyuanbianlitie.mp4)
  │
  ▼
PHALP（git repo brjathu/PHALP，uv add 装入主项目 .venv）
  │ 每帧每人 bbox + 跨切镜跟踪 ID
  ▼
HMR2.0（hmr2 包，4D-Humans repo 的 python 包，uv add 装入同一 .venv）
  │ 每帧每人 SMPL 参数（pose θ + shape β + 相机）
  ▼
我们写的 src/round1_motion/run_4dhumans.py（~80 行）
  │ 把上面两个串起来 + 按李小冉 ID 过滤
  ▼
src/round1_motion/smpl_to_bvh.py → 一段李小冉的 BVH
  │
  ▼
src/round1_motion/blender_retarget.py（被 blender --background --python 调用）
  │
  ▼
outputs/round1_motion/retarget/clip_friendly_retargeted.mp4
```

**"用别人 repo" 的 reframe**：装到 `.venv/site-packages/` 的代码，物理上跟"用 modelscope 包"没区别——都是依赖。差别仅在三点：

1. **来源**：modelscope 走 pypi，hmr2 / phalp 走 git URL（uv 原生支持，是合法依赖来源）
2. **维护质量**：modelscope 团队维护，hmr2 是论文 repo（论文发完可能停更）
3. **license**：modelscope Apache-2，hmr2 是学术非商业 license — 玩具项目不商用，不卡

**"4D-Humans 其他环节"在哪**：检测 + 跟踪 = PHALP（另一个 git repo，同样 uv add）；权重 ckpt = `hmr2.models.download_models()` 自动从 HuggingFace 拉到 `~/.cache/4DHumans/`；SMPL 解码 = SMPL_NEUTRAL.pkl（已下载 ✅）；配置 YAML = hmr2 包内置。**唯一缺的就是"把这些串起来的入口脚本"**——这正是 `src/round1_motion/run_4dhumans.py` 的作用，约 80 行 python，等价复现 4D-Humans 官方 `track.py` 的链路逻辑（不用它的 `track.py` 是因为它假定你 cwd 在 repo 根）。

---

## 1. 环境与目录布局

### 1.1 项目布局（全局 src，不在 docs 下放代码）

`docs/` 只放**文档+文档资源**；代码、测试、数据、输出全部走项目根的标准目录：

```
tlou-dance/                                      # 项目根
├── pyproject.toml                               # 主项目；新增 [project.optional-dependencies].round1
├── uv.lock                                      # commit
├── .gitignore                                   # 项目根；新增大媒体/ckpt/outputs 规则
├── src/
│   └── round1_motion/                           # 本轮代码（python package）
│       ├── __init__.py
│       ├── prepare_clip.py                      # ffmpeg 切 friendly/hard clip
│       ├── run_4dhumans.py                      # 主入口：PHALP + HMR2.0 → SMPL pkl
│       ├── smpl_to_bvh.py                       # SMPL → BVH（TDD 子模块）
│       └── blender_retarget.py                  # bpy 脚本（被 blender --bg --python 调用）
├── tests/
│   └── round1_motion/
│       ├── test_smpl_to_bvh.py                  # TDD
│       └── test_prepare_clip.py                 # TDD（时间码解析）
├── docs/
│   └── 1-动作捕捉调研/
│       ├── PROMPT.md
│       ├── PLAN.md
│       ├── SUMMARY.md                           # 阶段 3 产出
│       └── assets/                              # 仅文档资源（截图、对比图等），git track 小图
├── data/                                        # 全局数据目录，git ignore
│   └── round1_motion/
│       ├── raw/                                 # 软链 ~/Downloads/xinyuanbianlitie.mp4
│       ├── clip/                                # 切出的 friendly/hard clip mp4
│       ├── smpl_models/                         # 软链 ~/Downloads/basicModel_neutral_lbs_*.pkl
│       └── rig/                                 # Mixamo Y-Bot fbx 等
└── outputs/                                     # 全局输出目录，git ignore
    └── round1_motion/
        ├── smpl/                                # 4D-Humans 输出 (.pkl)
        ├── bvh/                                 # 转换出的 .bvh
        └── retarget/                            # Blender 渲染 mp4 + .blend
```

**为什么 data/ 与 outputs/ 也在项目根而非 docs/1-…/ 下**：它们是**项目运行时数据**，不是文档资源；按惯例放项目根，per-round 用子目录隔离。docs 只承担"人读的文档"职责。

### 1.2 主项目 pyproject.toml 增量

**不**起 nested uv 子项目；重磅依赖通过 `[project.optional-dependencies]` 软隔离——默认 `uv sync` 不装，做 round 1 时跑 `uv sync --extra round1` 才触发。

需要在项目根 `pyproject.toml` **新增**以下段（其余保持现状）：

```toml
[project.optional-dependencies]
round1 = [
    "torch==2.5.1",                   # Constitution 钉死 cu121
    "torchvision",
    "torchaudio",
    "smplx",                          # SMPL 解码
    "opencv-python",
    "ffmpeg-python",
    "numpy<2",                        # 兼容 4D-Humans 旧 API
    "tqdm",
    "hmr2 @ git+https://github.com/shubham-goel/4D-Humans.git",
    "phalp @ git+https://github.com/brjathu/PHALP.git",
    "detectron2 @ git+https://github.com/facebookresearch/detectron2.git",
]

[[tool.uv.index]]
name = "tsinghua"
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
default = true

[[tool.uv.index]]
name = "aliyun-torch"
url = "https://mirrors.aliyun.com/pytorch-wheels/cu121/"
explicit = true

[tool.uv.sources]
torch = { index = "aliyun-torch" }
torchvision = { index = "aliyun-torch" }
torchaudio = { index = "aliyun-torch" }
```

**装载时机**：阶段 0 末尾跑一次 `uv sync --extra round1` 触发全部安装（包括 4D-Humans / PHALP / detectron2 from git）。后续轮次（round 2+）默认 `uv sync` 不会带这些重磅依赖。

**未来轮次约定**：若 round 2 也有重磅依赖，新加 `[project.optional-dependencies].round2 = [...]`，互不影响。

### 1.3 Blender

- **Blender 4.5.9 LTS** ✅（你已装；4.5 LTS 长期支持到 2027）
- **不**需要把 `bpy` 装进 .venv——Blender 自带 Python 已能 `import bpy`。脚本走 `blender --background --python src/round1_motion/blender_retarget.py -- <args>` 调用，与项目 uv 完全解耦。
- 验证：`blender --version` 应输出 `Blender 4.5.x`。

---

## 2. 阶段详细计划

### 阶段 0 — 环境与素材准备（预算 4 小时）

**前置（用户已完成）**：

- [x] 源视频：`~/Downloads/xinyuanbianlitie.mp4`
- [x] Blender 4.5.9 LTS
- [x] SMPL_NEUTRAL.pkl：`~/Downloads/basicModel_neutral_lbs_10_207_0_v1.0.0.pkl`（SHA256 ✅ 校验通过）

**Agent 端动作**：

- [ ] 项目根 `pyproject.toml` 新增 `[project.optional-dependencies].round1` + uv 索引段（§1.2）
- [ ] 建 `src/round1_motion/__init__.py`、`tests/round1_motion/__init__.py`
- [ ] 建 `data/round1_motion/{raw,clip,smpl_models,rig}/`、`outputs/round1_motion/{smpl,bvh,retarget}/`
- [ ] 项目根 `.gitignore` 新增大媒体/ckpt/outputs 规则（§6）
- [ ] 软链：`data/round1_motion/raw/source.mp4` → `~/Downloads/xinyuanbianlitie.mp4`
- [ ] 软链：`data/round1_motion/smpl_models/SMPL_NEUTRAL.pkl` → `~/Downloads/basicModel_neutral_lbs_10_207_0_v1.0.0.pkl`
- [ ] `uv sync --extra round1` 装全部依赖（首跑会从 git 拉 hmr2 / phalp / detectron2，可能 5-10 分钟）
- [ ] 写 `src/round1_motion/prepare_clip.py`，从源视频里切：
  - `data/round1_motion/clip/friendly_10s.mp4`：李小冉为画面主体、低切镜、低遮挡（首选副歌某段稳定机位）
  - `data/round1_motion/clip/hard_10s.mp4`：切镜复杂段（stretch goal）

**出口**：`uv sync --extra round1` 不爆 + friendly clip 存在。

### 阶段 1 — 4D-Humans 跑 SMPL 序列（预算 1 天）

**核心**：`src/round1_motion/run_4dhumans.py`，~80 行，等价复现 4D-Humans 官方 `track.py`。

**步骤**：

1. 首跑会自动下载 HMR2.0b 权重到 `~/.cache/4DHumans/`（可能科学上网；如不行从 hf-mirror.com 手动下）
2. `run_4dhumans.py` 骨架：
   ```python
   from hmr2.models import load_hmr2, download_models, DEFAULT_CHECKPOINT
   from phalp.trackers.PHALP import PHALP
   # 1. download_models() 触发 ckpt 拉取
   # 2. PHALP.track(video_path) → 拿 per-frame {bbox, tracking_id, smpl_params}
   # 3. 落到 outputs/round1_motion/smpl/friendly_smpl.pkl
   ```
3. 跑 friendly clip → `outputs/round1_motion/smpl/friendly_smpl.pkl`（含 24×3 axis-angle pose, 10 shape, 跨帧 tracking ID）
4. **挑出李小冉的 tracking ID**：人工指认（看 PHALP 渲出的 tracklet 视频，肉眼判断哪个 ID 对应李小冉）
5. 过滤出李小冉单人序列 → `outputs/round1_motion/smpl/friendly_lxr.pkl`
6. 如时间允许，对 hard clip 重复一遍，对比切镜场景下 ID 是否碎成多个

**已知踩坑预案**（命中即降级）：

| 风险 | 概率 | 降级 |
| --- | --- | --- |
| `detectron2 @ git+...` CUDA 版本不匹配装不上 | 中 | 退到 SMPLer-X：替换 round1 extra 里 hmr2/phalp/detectron2 → `smplerx @ git+https://github.com/caizhongang/SMPLer-X.git` |
| numpy 2.x 与 hmr2 冲突 | 中 | 已 pin `numpy<2` |
| `~/.cache/4DHumans/` 自动下载需要科学上网 | 中 | 从 hf-mirror.com 手动下放到对应目录 |
| 24GB 显存 OOM（PHALP+HMR2+ViTDet 同载） | 低 | 拆步骤：先 PHALP 单跑出 detection track 落盘 → 再 HMR2 单独跑 |
| 切镜样本李小冉 ID 碎成多个 | 中 | friendly clip 优先证明可行；hard 转 stretch goal |

### 阶段 2 — SMPL → BVH → Blender retarget（预算 4 小时）

**步骤**：

1. **SMPL → BVH**：`src/round1_motion/smpl_to_bvh.py`（基于开源参考 [SMPL-to-BVH](https://github.com/KosukeFukazawa/smpl2bvh) 或自写 ~50 行：SMPL 24 关节 axis-angle → BVH HIERARCHY + MOTION）。**TDD 子模块**（见 §3）。
2. **导入 Blender**：`src/round1_motion/blender_retarget.py`（bpy）：
   - 加载 BVH armature
   - 加载 retarget 目标 rig（首选 Mixamo Y-Bot fbx，骨骼 ~65 根，命名规范；备选 Blender 4.5 自带 Rigify metarig）
   - bpy 骨骼名映射 + Copy Rotation 约束自写 retarget（最朴素也最可控）
   - 调用：`blender --background --python src/round1_motion/blender_retarget.py -- --bvh outputs/round1_motion/bvh/friendly_lxr.bvh --out outputs/round1_motion/retarget/friendly.mp4`
   - 渲 30 fps mp4 → `outputs/round1_motion/retarget/friendly_retargeted.mp4`
3. **判定**（来自 PROMPT 出口指标）：
   - 起手动作可辨：✅/❌
   - 副歌主要 8 拍可辨：✅/❌
   - 无明显穿模 / 关节 180° 翻转：✅/❌
   - 无毛刺式抖动（>10° / 帧）：✅/❌

### 阶段 3 — SUMMARY.md（半小时）

按 Constitution 模板：

- 开发项背景（直接引 PROMPT.md）
- 实现方案
  - **关键决策**：为什么走 4D-Humans library-style 而非 modelscope（事实证据见 §0.2）
  - 开发内容概括（实际跑了哪些组件、用了多少时间）
  - 额外产物：clip 路径、SMPL pkl 路径、retarget mp4 路径、调试脚本
- 局限性：精度、多人 ID 准确性、retarget 后细节缺失（手指 / 表情 / 物理）
- 后续 TODO：精度优化、多人完整 retarget、风格化、与 round 0 拿到的 TLOU 主角模型联调

---

## 3. 测试策略（Constitution TDD 例外说明）

Constitution 要求"业务逻辑 / 纯函数 / 算法"先写测试。本轮多数代码属 Constitution 列出的**例外**（"探索性原型 + 与外部系统的集成"——4D-Humans 调用、bpy 脚本），先跑通再补 smoke test。

但有两个**纯函数**子模块**必须 TDD**：

- `src/round1_motion/smpl_to_bvh.py` 的关节角度转换（SMPL axis-angle → BVH ZXY Euler）：
  - 测试用例：单位旋转 / 绕 X、Y、Z 各 90° 已知值 / 随机往返一致性
  - 文件：`tests/round1_motion/test_smpl_to_bvh.py`
- `src/round1_motion/prepare_clip.py` 的时间码解析（`HH:MM:SS.mmm` → 秒）：
  - 测试用例：完整时间码 / 缺时分缺秒 / 负值/越界报错
  - 文件：`tests/round1_motion/test_prepare_clip.py`

跑测试：`uv run pytest tests/round1_motion/`。

---

## 4. 时间与硬度判定

| 阶段 | 预算 | 累计 | 判定点 |
| --- | --- | --- | --- |
| 0 | 4h | 4h | `uv sync --extra round1` 不爆 + clip 切好 |
| 1 | 8h | 12h（D1.5） | friendly clip 上拿到李小冉 SMPL 序列 |
| 2 | 4h | 16h（D2 完） | retarget mp4 出来 |
| 3 | 0.5h | +0.5h | SUMMARY |

**总预算**：~16.5h，逼近 issue 上限 2 天。

**踩坑超时**（detectron2 装不上 + 重选 SMPLer-X）：超时即不再硬刚，写 SUMMARY 标记"未在 2 天内拿到端到端结果，建议下一轮换 EasyMocap 或继续 SMPLer-X 路径"——**仍然算 spike 出结论**（出结论本身就是 spike 的目的）。

---

## 5. 风险与降级矩阵

| 风险 | 影响 | 降级 |
| --- | --- | --- |
| `detectron2 @ git+...` CUDA 版本不匹配 | 阶段 0 阻塞 | 切 SMPLer-X：替换 round1 extra 里相关 git 依赖 |
| 4D-Humans 权重自动下载需要科学上网 | 阶段 1 阻塞 | 从 hf-mirror.com 镜像手动下载到 `~/.cache/4DHumans/` |
| 切镜样本李小冉 tracking ID 碎成多个 | 阶段 1 输出不可用 | 退到 friendly 单镜头样本，先证可行 |
| SMPL → BVH 关节映射出错 → retarget 后人变形 | 阶段 2 阻塞 | 先用 SMPL-to-BVH 开源参考实现保底；手写版作为 stretch |
| Blender retarget 骨骼映射手工开销大 | 阶段 2 超时 | 改用 Rokoko Studio Live 插件 GUI 拖拽（5 分钟）；记录在 SUMMARY |
| 24GB GPU OOM | 阶段 1 阻塞 | 拆步骤：PHALP 单跑落盘 → HMR2 单独跑 |

---

## 6. .gitignore 增量（落到项目根 .gitignore）

在现有 .gitignore 末尾**新增**段（不修改既有规则）：

```gitignore
# === round 1 / motion-extract & 通用大件 ===
# 项目运行时数据 / 输出（per-round 子目录隔离）
data/
outputs/

# 大媒体 / 模型权重通用扩展名
*.mp4
*.bvh
*.fbx
*.pkl
*.pth
*.ckpt
*.blend
*.blend1
*.glb

# docs/ 资源里如有大图也忽略（小 PNG/SVG 仍可 commit）
docs/**/assets/*.mp4
docs/**/assets/*.mov
```

---

## 7. 关键文件路径速查

| 文件 | 作用 |
| --- | --- |
| `pyproject.toml` | 主项目；新增 `[project.optional-dependencies].round1` 段 |
| `src/round1_motion/__init__.py` | round 1 包 marker |
| `src/round1_motion/prepare_clip.py` | 阶段 0 切片 |
| `src/round1_motion/run_4dhumans.py` | 阶段 1 主入口（~80 行复现 track.py 链路） |
| `src/round1_motion/smpl_to_bvh.py` | 阶段 2 SMPL → BVH（TDD） |
| `src/round1_motion/blender_retarget.py` | 阶段 2 bpy 脚本 |
| `tests/round1_motion/test_smpl_to_bvh.py` | TDD |
| `tests/round1_motion/test_prepare_clip.py` | TDD |
| `data/round1_motion/raw/source.mp4` | 软链 → ~/Downloads/xinyuanbianlitie.mp4 |
| `data/round1_motion/clip/friendly_10s.mp4` | 阶段 0 产出 |
| `data/round1_motion/smpl_models/SMPL_NEUTRAL.pkl` | 软链 → ~/Downloads/basicModel_neutral_lbs_*.pkl |
| `outputs/round1_motion/smpl/friendly_lxr.pkl` | 阶段 1 产出 |
| `outputs/round1_motion/bvh/friendly_lxr.bvh` | 阶段 2 中间产物 |
| `outputs/round1_motion/retarget/friendly_retargeted.mp4` | 阶段 2 最终产出 |
| `docs/1-动作捕捉调研/PROMPT.md` | 需求源 |
| `docs/1-动作捕捉调研/PLAN.md` | 本文件 |
| `docs/1-动作捕捉调研/SUMMARY.md` | 阶段 3 产出 |

---

## 8. 出口检查清单（用于阶段 3 收尾自查）

- [ ] friendly clip mp4 存在
- [ ] friendly clip 上李小冉的 SMPL 序列 .pkl 存在
- [ ] retarget 后的 mp4 存在
- [ ] SUMMARY.md 写完，含决策、关键 finding、局限、后续 TODO
- [ ] `pyproject.toml` 与 `uv.lock` 已 commit（重磅大件全 ignore）
- [ ] TDD 子模块测试 `uv run pytest tests/round1_motion/` 全绿
- [ ] commit message 含 `Closes #2`
- [ ] BACKLOG.md 删除 #2 那一行
- [ ] PR 描述贴 retarget 视频片段（可截 gif）
