# SUMMARY —— Round 1 motion-extract spike

> 关联：[PROMPT.md](./PROMPT.md) / [PLAN.md](./PLAN.md) / [GitHub #2](https://github.com/pkulijing/tlou-dance/issues/2)
>
> **结论：spike 失败终止**。前置 pipeline（detection + tracking + HMR2 推理）已完整跑通；卡死在 4D-Humans 内置的 pyrender 渲染阶段。**未拿到可用的 SMPL/BVH/FBX 动作序列**，未做 retarget。

## 一、背景

PROMPT 待回答的核心问题：能否从《心愿便利贴》舞蹈视频（多人 + 切镜 + 半身镜头多）提取出可驱动 3D 人形 rig 的动作序列？

按 PLAN 走 4D-Humans（PHALP tracker + HMR2 单帧重建）路线，目标 friendly 10s clip → SMPL pkl → BVH → Blender retarget → 渲一段对照视频。

## 二、实际走到哪一步

| 阶段 | 状态 | 备注 |
|---|---|---|
| 视频预处理（10s clip 切片） | ✅ | `data/round1_motion/clip/friendly_10s.mp4`（00:52–01:02，王蒙居中半身） |
| Python 环境（hmr2 / phalp / detectron2 / chumpy / NMR） | ✅ | uv sync 过，299 包，CUDA 12.1 + RTX 4090 可用 |
| 权重就位（HMR2 ckpt / SMPL / ViTDet / mask_rcnn / hmar / pose_predictor / ...） | ✅ | 从 hf-mirror（camenduru/4D-Humans）+ cs.utexas.edu（PHALP 专属）合计 ~6 GB |
| `track_video.py` 启动 | ✅ | hydra 配置就绪 |
| Detection + Tracking（PHALP） | ✅ | log 显示进度跑过 50% 帧（被 EGL 错误中断时已处理 ~165 帧） |
| HMR2 SMPL 推理 | ✅ | 推理路径在 EGL 错误前已执行多次（每帧推理后立刻渲染） |
| **pyrender 渲染** | ❌ | EGL 路径反复 reset_render 后 EGL_BAD_MATCH；改 pyglet GLX 路径后整 process hang（CPU 99% 但无产出） |
| SMPL pkl 持久化 | ❌ | PHALP 每帧渲完才 `save tracks`；render 崩，pkl 一个没落盘 |
| Blender retarget | ❌ | 跳过 |

## 三、主要踩坑 + 解法

按"基础设施层 → 应用层"顺序：

### 1. Python 依赖图（基础设施层）

| 问题 | 解法（落在 `pyproject.toml`） |
|---|---|
| chumpy 0.70 上游 setup.py 引用已废弃的 packaging 工具内部 API，build 失败 | `[tool.uv.sources] chumpy = { git = "https://github.com/umautobots/chumpy.git", rev = "25c2019..." }` |
| uv 0.11.x 的 `[tool.uv.extra-build-dependencies]` 实测对**所有**包（直接/间接）都不生效 | 改用 `[[tool.uv.dependency-metadata]]` 手抄 5 个 git+ 包的 `install_requires`，**跳过 metadata 阶段调 setup.py** |
| `neural-renderer-pytorch` 是 hmr2 的间接依赖，间接依赖即使配 dependency-metadata 也要先升为直接依赖 | 显式列入 `round1` extras |
| hatchling 默认禁 `<name> @ git+...` 形式 | `[tool.hatch.metadata] allow-direct-references = true` |
| setuptools 81+ 把 `pkg_resources` 整个移除，detectron2 0.6 在 `model_zoo/__init__.py` import 它会崩 | 钉死 `setuptools<81` |
| aliyun pytorch-wheels CDN 在密集请求后 IP 进黑名单（403） | 改走 `download.pytorch.org/whl/cu121`（Constitution 推荐路在解禁后再切回） |
| pytest 把 `tests/round1_motion/` 当成跟 `src/round1_motion/` 同名的包，遮蔽 src | 删 `tests/round1_motion/__init__.py`（让 pytest rootdir-based 不当 package） |

### 2. 权重 cache 路径分散（基础设施层）

不同组件期望不同的 cache 路径，**当初下载时按 `camenduru/4D-Humans` HF repo 镜像结构堆 `~/.cache/4DHumans/` 顶层是错的**——应该一开始就 grep 各组件 download 函数确认期望路径，分别 `--local-dir`：

| 组件 | 期望 cache 路径 |
|---|---|
| `hmr2` | `~/.cache/4DHumans/{logs,data,model_final_f05665.pkl}` |
| `phalp` | `~/.cache/phalp/{3D,weights,ava}/...`（11 个文件，从 `cs.utexas.edu` 下） |
| `detectron2` (`iopath`) | `~/.torch/iopath_cache/<URL 路径完整 mirror>/...` |

最后用一坨 `ln -s` 把已下文件 link 到对应路径绕过——**ad-hoc 修补，下次不应再犯**。

### 3. 视频切片（应用层）

`ffmpeg` 默认 re-encode 路径在某些 1080p h264 输入上 `libx264` SIGSEGV（`-ss` 放在 `-i` 之后的 output-side seek 触发）。修法：双重 seek（input-side 粗 seek 到关键帧 + output-side 微调 1s 到精确起点），既精确又避开崩溃。固定在 [scripts/round1_motion/prepare_clip.py](../../src/round1_motion/prepare_clip.py) 的 `cut_clip` 函数。

### 4. PHALP 自动下载链接失效（应用层）

PHALP 的 `cached_download_from_drive()` 写死从 `github.com/classner/up/raw/master/...` 下 SMPL pkl，但该路径已 404。改为预放 `~/.cache/phalp/3D/models/smpl/SMPL_NEUTRAL.pkl`（symlink 到 4D-Humans 自带的 chumpy-free 版），让 PHALP 看到文件存在跳过下载。

### 5. pyrender 渲染（应用层 —— spike 卡死的真正点）

PHALP / hmr2 三个文件都强设 `os.environ['PYOPENGL_PLATFORM'] = 'egl'`：
- `phalp/visualize/py_renderer.py:3`（无条件赋值）
- `hmr2/utils/{mesh_renderer,renderer}.py`（条件赋值，但 import 时机最早，先抢到）

**EGL 路径**：在 RTX 4090 + DISPLAY 已设的环境下，`pyrender` 反复 `reset_render`（del + 新建 OffscreenRenderer）多次后 `eglMakeCurrent` 失败 (`err=12289 EGL_BAD_MATCH`)。前面跑到 55% 才崩。Minimal pyrender 测试（单进程 < 5 次 render）OK——崩点跟反复 reset 有关。

**pyglet GLX 路径**：把三个文件都 patch 成"DISPLAY 已设时不强设 EGL"，pyrender 默认走 pyglet。Minimal 测试 OK，但实际 demo 跑时整个 process **hang 在某个 X 调用上**（CPU 99% 8+ 分钟，log 完全静止，无 X server 错误）。可能跟 GNOME 桌面合成器在 :1 上抢 OpenGL context 有关。

**未尝试的备选**（spike 终止于此）：
- **OSMesa（CPU 软渲染）**：需 `sudo apt install libosmesa6 libosmesa6-dev`，预计 30-45 分钟跑完 300 帧，最稳但慢。
- **xvfb-run + 虚拟 X**：需 `sudo apt install xvfb`，让 pyglet 走纯 xvfb 不碰 :1。
- **`render.enable=False` 跳过渲染**：能拿 SMPL pkl，需自己用 Blender 渲染验证 sanity。

## 四、实质产出（可复用）

留给后续轮次的资产：

| 路径 | 内容 | 复用价值 |
|---|---|---|
| [pyproject.toml](../../pyproject.toml) | 完整 round1 deps + chumpy 重定向 + dependency-metadata 全套 + uv index | 重新搞 4D-Humans 环境无需再踩这堆坑 |
| [src/round1_motion/prepare_clip.py](../../src/round1_motion/prepare_clip.py) | timecode 解析（27 单测）+ ffmpeg 双重 seek 切片 | 通用视频切片工具 |
| [scripts/round1_motion/track_video.py](../../scripts/round1_motion/track_video.py) | 4D-Humans 上游 `track.py` 的 worktree 副本 | hmr2 包不带 entry，必须本地落一份 |
| `~/.cache/4DHumans/`（用户机器） | HMR2 ckpt + ViTDet + SMPL_NEUTRAL（chumpy-free） | 5.3 GB，下次再尝试时无需重下 |
| `~/.cache/phalp/`（用户机器） | PHALP 全套 11 个权重 + symlinks | ~370 MB |
| `~/.torch/iopath_cache/`（用户机器） | mask_rcnn_X_101 + ViTDet symlink | detectron2 model zoo 命中 |
| `data/round1_motion/clip/friendly_10s.mp4` | 切好的 friendly 10s 片段 | 后续路径直接复用 |
| `data/round1_motion/raw/xinyuanbianlitie_full.mp4` | 完整源片段（3:58.10，stream-copy 已去版权尾） | 备用 |
| `tests/round1_motion/test_prepare_clip.py` | 27 单测（parse_timecode 全覆盖） | TDD 实践记录 |

## 五、对 PROMPT 出口指标的回答

| 出口 | 状态 |
|---|---|
| 选定 SOTA 单目视频 mocap 方案 | ✅ 选 4D-Humans（PHALP + HMR2.0），并落地了完整环境 |
| 跑完一段 10s clip 出标准动作格式 | ❌ 卡在 pyrender，**未拿到 SMPL pkl** |
| 在 Blender retarget + 渲对照视频 | ❌ 未到这步 |
| 给出**多人 + 切镜可行性**结论 | ⚠️ **无定论**——4D-Humans 的 detection + tracking + HMR2 推理路径完整可跑（前 50% 帧无 EGL 错），算法能力上没暴露问题；卡死在工程层面（pyrender 在本机 RTX 4090 + GNOME 桌面下不稳）。多人/切镜在此 spike 中**未真正测过**。 |

## 六、局限性 / 未解决问题

1. **pyrender EGL/GLX 在本机都不稳**：spike 终止时未试 OSMesa / xvfb / 关 render 三条备选路径之一。算法层的多人/切镜可行性结论没拿到。
2. **半身镜头限制未验证**：友好样本本身就是半身（00:52–01:02 王蒙居中半身），下半身姿态预期偏猜测；但因没拿到 pkl 没法实测。
3. **依赖图的复杂度劝退**：`pyproject.toml` 里 dependency-metadata + sources + extra-build-dependencies + no-build-isolation 加起来 50 行+ 配置，全部是为了让 2022/2023 年的 chumpy/NMR/detectron2/hmr2/phalp 在 2026 年的 setuptools/uv/Python 3.12 上 build。任何上游一个 commit 都可能让这套配置失效。
4. **PHALP 内部 cache 路径写死且链接老化**：`github.com/classner/up` 的 SMPL 链接已 404，PHALP 没维护。后续 PHALP 自动下载链接还会进一步腐烂。

## 七、后续 TODO（按下次重启 spike 时优先级）

1. **先试 `render.enable=False` 拿 SMPL pkl**（最快路径，不依赖渲染就能完成 PROMPT 第 2 条出口）：
   ```
   uv run python scripts/round1_motion/track_video.py \
       video.source=... video.output_dir=... \
       video.end_frame=300 render.enable=False
   ```
   预期 1-3 分钟出 `outputs/.../results/friendly_10s/*.pkl`，包含每个 track id 的 SMPL 参数序列。
2. **拿 pkl 后用自己写的 Blender 脚本渲染**（不依赖 PHALP 的 pyrender），同时做 retarget 到 mannequin。这一步**也是 round 2/3 实际要做的事**——PHALP 内置 render 只是 sanity check，最终视频生产路径必然走 Blender。
3. **如果 #1 也挂**（HMR2 推理本身就有问题），再装 OSMesa 或 xvfb 走稳健渲染，看 pkl 能不能产出。
4. **算法可行性结论必须重新跑**：换一段全身可见的 friendly clip（如果有）跟现在这段半身做对照，看下半身姿态准度对最终舞蹈观感的影响。
5. **避免再踩**：所有第三方 cache 路径在动手下载前**必须先 grep 各组件下载函数**，不要按 HF repo 镜像目录结构盲下。

## 八、对项目主线的影响

- motion-extract 这条 P0 闸门**未通过**。但前置算法链路完整，工程坑都已踩过且文档化，**重启 spike 的成本已大幅下降**（环境就绪 + 权重就位 + clip 切好），最快路径只需跑一次 `render.enable=False` 即可拿到 SMPL pkl 验证算法层可行性。
- 整体项目（asset-extract round 0 + motion-extract round 1）保留 GO/NO-GO 状态，决策推后到 round 2（如果重启 spike）或新一轮 spike。
