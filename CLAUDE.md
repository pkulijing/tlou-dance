# tlou-dance

玩具项目：从本地安装的《The Last of Us》游戏中提取主角人物模型和关键场景，从《浪姐 7》李小冉组《心愿便利贴》舞蹈视频中提取人物动作，最终驱动游戏人物跳这支舞，做一段整活视频。

## 目录结构

- `docs/<N>-<中文>/` —— 每轮一目录，含 PROMPT/PLAN/SUMMARY 三件套；只放文档，**不放代码、不放重数据**
- `docs/BACKLOG.md` / `docs/DEVTREE.md` —— 跨轮索引与开发树
- `scripts/blender/` —— 项目代码（Blender headless Python 工具）；非 Blender 类放 `scripts/` 直下
- `data/round-N/{raw,intermediate,normalized}/` —— 实验数据；raw 大多 gitignored 但留 INVENTORY.md 含 URL 可重下；normalized 是真正成品（`*.fbx` 走 git-lfs）
- `.github/` `.gitlab/` `.vscode/` `pyproject.toml` `.pre-commit-config.yaml` `.gitattributes` —— 模板/CI/编辑器/Python/git-lfs 配置

## 开发注意事项

- 本项目使用 Python + uv 管理依赖，遵循全局 Constitution 中的 Python 开发规则（`uv add` / `uv run` / 清华 pypi 源等）。
- Blender 用 4.5.x LTS（4.5.9 测试通过），脚本走 `blender --background --python scripts/blender/<x>.py -- <args>` 调用。
- `*.fbx` 全部走 git-lfs（项目根 `.gitattributes` 已配）；新增重数据格式（`.blend` / `.dds` 之类）按需扩。
- raw 资产 archive 体积大（单角色 ~150MB），全部 gitignored；下载脚本与 URL 见 `data/round-N/raw/INVENTORY.md`。
