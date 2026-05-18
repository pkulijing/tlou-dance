# tlou-dance

玩具项目：从本地安装的《The Last of Us》游戏中提取主角人物模型和关键场景，从《浪姐 7》李小冉组《心愿便利贴》舞蹈视频中提取人物动作，最终驱动游戏人物跳这支舞，做一段整活视频。

## 目录结构

```
tlou-dance/
├── docs/                     # 文档（每轮一目录，数字前缀+中文描述）
│   ├── BACKLOG.md             # 未关闭 issue 扁平索引
│   ├── DEVTREE.md             # 开发树（轮次依赖可视化）
│   └── 0-游戏人物模型提取调研/
│       ├── PROMPT.md          # 需求（多由 GitHub issue 驱动）
│       ├── PLAN.md            # 实施计划
│       ├── SUMMARY.md         # 总结
│       ├── inspect-output/    # Blender headless 脚本输出
│       └── assets/screenshots/  # 文档配图
├── scripts/                   # 项目代码
│   ├── blender/               # Blender headless Python 工具
│   │   ├── inspect_model.py    # 检查 mesh / armature / texture
│   │   ├── merge_for_mixamo.py # 多部件 FBX 合并 + 剥骨 → Mixamo 输入
│   │   └── wire_textures_into_normalized.py  # KD-tree 部件分配 + PBR 材质 + 导出
│   └── texture_wiring/        # 纯逻辑模块（无 bpy，可被 pytest 复用）
│       ├── texture_parser.py   # 扫 Textures 目录识别 PBR 通道 + 自动探测主前缀
│       ├── part_assigner.py    # numpy chunked KD-tree 最近邻匹配
│       └── alias.py            # Tess submesh / cloth-sim 附件别名表
├── tests/                     # pytest 单元测试（覆盖 scripts/texture_wiring/）
├── data/                      # 实验数据（绝大部分本地、gitignored）
│   ├── round-0/
│   │   ├── raw/               # fan-port 原档（INVENTORY 留链接，archive 不入 git）
│   │   ├── intermediate/      # 中间产物 .blend，全 gitignored
│   │   └── normalized/        # 最终成品 .fbx（git-lfs 管理）
│   └── round-2/
│       └── normalized/        # 贴图集成 dry-run 产物（gitignored）
├── .github/                   # issue 模板 / labels / CI（GitHub）
├── .gitlab/                   # issue 模板（GitLab，双轨保留）
├── .vscode/                   # 编辑器配置（formatOnSave / 推荐扩展）
├── pyproject.toml             # Python deps（uv 管理 + ruff 配置）
├── .pre-commit-config.yaml    # commit 前 lint 闸门
├── .gitattributes             # `*.fbx` 走 git-lfs
└── .cc-template.yml           # 跨项目共享配置 marker
```

## 开发流程

本项目遵循 [全局 Constitution](~/.claude/CLAUDE.md) 中的「需求 - 计划 - 执行 - 总结」四步开发模式：

- **需求** → [`docs/<N>-<中文描述>/PROMPT.md`](docs/)（多由 GitHub issue 驱动 `/start <issue#>` 写入）
- **计划** → 同目录 `PLAN.md`（plan mode 输出）
- **执行** → Agent 主导，必要时人类干预；先写测试再写实现（TDD），探索性原型例外
- **总结** → 同目录 `SUMMARY.md`，commit body 含 `Closes #N` 自动关 issue

未来计划见 [`docs/BACKLOG.md`](docs/BACKLOG.md)；轮次依赖关系见 [`docs/DEVTREE.md`](docs/DEVTREE.md)。

## 当前状态

- ✅ Round 0：[游戏人物模型提取调研](docs/0-游戏人物模型提取调研/SUMMARY.md) —— 三人 mixamorig 标准化骨架灰模就绪
- 🔄 Round 1（worktree 并行中）：P0 spike [#2 视频动作提取](https://github.com/pkulijing/tlou-dance/issues/2)
- ❌ Round 2：[贴图集成 spike 失败](docs/2-贴图集成进normalized-FBX/SUMMARY.md) —— pipeline + 41 单测就位，但 Blender 4.5 不解 TLOU DDS 子格式；[#3](https://github.com/pkulijing/tlou-dance/issues/3) 保持 open，等外部 DDS 解码方案落地后重启
