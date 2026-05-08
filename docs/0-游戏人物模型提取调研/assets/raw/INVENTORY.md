# Round 0 Raw Assets — Inventory

raw archive 体积总计 ~1.5 GB，**不入 git**（同级 `.gitignore`）。本文件记录来源 + 内容 + license，方便重新下载与可重复性追溯。

下载脚本：见 SUMMARY.md 末尾或 `inspect-output/*.txt` 头部，全部走 Yandex Disk public API → curl。

## 三个角色全部来自同一艺术家 Crazy31139（DeviantArt）

同源好处：同样的 ND 原骨骼命名（`root/spinea/spineb/spinec/spined/neck/heada/headb/l_eyeball...`）、同样的多部件 FBX + 分离 .dds 贴图结构 → Phase 1 retarget / 贴图 wiring 可批量套用同一脚本。

## Joel — TLOU2 Joel (Jackson)

- **Source page**: https://www.deviantart.com/crazy31139/art/TLOU2-Joel-Jackson-854239224
- **Yandex Disk public**: https://disk.yandex.ru/d/-fiWKh4kzwa66g
- **Archive**: `joel-tlou2-jackson.rar`，119 MB（解压后 ~728 MB）
- **结构**：
  - `TLOU2 - Joel (Jackson)/*.fbx` × 7（body / head / pants / hair-cloth / backpack / backpack-jacket-cloth / backpack-strap-cloth）
  - `TLOU2 - Joel (Jackson)/ASCII/*.ascii` × 11（XPS 格式备份）
  - `TLOU2 - Joel (Jackson)/SMD/*.smd` × 11（Source 引擎格式备份）
  - `TLOU2 - Joel (Jackson)/Textures/<部件>/` × 200+ .dds 贴图
  - `TLOU2 - Joel (Jackson)/Scene.tbscene`（Marmoset Toolbag 场景文件，可忽略）
- **检查结果**（见 `../inspect-output/joel.txt`）：
  - 7 个 armature（每部件一份独立副本，**Phase 1 需要清理**只保留主 body armature）
  - 主 armature：1548 bones，ND 原命名
  - 总计 ~111k verts / 162k faces

## Ellie — TLOU2 Ellie (Seattle)

- **Source page**: https://www.deviantart.com/crazy31139/art/TLOU2-Ellie-Seattle-853552008
- **Yandex Disk public**: https://disk.yandex.ru/d/kAS7GBRC7xSOBw
- **Archive**: `ellie-tlou2-seattle.rar`，195 MB
- **结构**：
  - `TLOU2 - Ellie (Seattle)/*.fbx` × 12（body / head / arms / hair-cloth / jacket-cloth / backpack / backpack-zip-cloth / bracelet / bandage / bandage-forearm / leg-holster / strand-hair-cloth + flashlight + gas-mask 配件）
  - `TLOU2 - Ellie (Seattle)/ASCII/*.ascii`（同款备份）
  - `TLOU2 - Ellie (Seattle)/Textures/`
- **检查结果**（见 `../inspect-output/ellie.txt`）：
  - 6 个 armature（含 hair-cloth / jacket-cloth 物理 sub-rig）
  - 主 armature：1845 bones，ND 原命名
  - 总计 ~84k verts / 134k faces（仅采样了 6/12 部件）

> 历史记录：本轮原本下载了 Open3DLab FrankDP1 的 Part I Ellie .blend（112 MB），检查发现是 Rigify+FaceitRig 改装版、与 Joel/Tess 骨骼不一致 + 79 个贴图死链 + 疑似 young Ellie。**已弃**，切到本节这份。

## Tess — TLOU Part 1 Tess

- **Source page**: https://www.deviantart.com/crazy31139/art/TLOU-Part-1-Tess-956024857
- **Yandex Disk public**: https://disk.yandex.ru/d/tuf2raTQLizNfw
- **备选 Google Drive**: https://drive.google.com/file/d/1jqi8T8D9osXGIBTASHZxejL0Hy3nuUvu/view?usp=sharing
- **Archive**: `tess-tlou-part1.rar`，149 MB（解压后 ~682 MB）
- **结构**：
  - `TLOU Part1 - Tess/tess.mesh.fbx`（**已合并版**，Phase 1 直接用这个，比 Joel/Ellie 省事）
  - `TLOU Part1 - Tess/FBX/*.fbx` × 6（分部件备份）
  - `TLOU Part1 - Tess/ASCII/*.mesh.ascii` × 6
  - `TLOU Part1 - Tess/Textures/` × 200+ .dds（注意：**含若干 `ellie-*` 命名的贴图** —— 是 ND 在 Part 1 内 Tess 与 Ellie 共享 SSS / 表皮贴图集，正常现象）
- **检查结果**（见 `../inspect-output/tess.txt`）：
  - 1 个 armature（已合并）：1918 bones，ND 原命名
  - 总计 ~150k verts / 217k faces

## License / Fair use

三份都属 fan port —— 原始资产版权归 Naughty Dog / Sony Interactive Entertainment。Crazy31139 在每页都注明：

> "I do not own the rights to these models. Please do not use them for commercial purposes."

本项目（玩具 / 个人非商业整活视频）落入典型 fan use 范畴：

- **可以**：本地使用、retarget、做视频上传至 B 站 / YouTube 等社区平台
- **应当**：在最终视频说明 / SUMMARY.md 中注明 Naughty Dog / Crazy31139 出处
- **不应当**：再分发原始模型文件、不应该将基于此模型的内容商业销售

## 重新下载脚本（参考）

```bash
# Joel
URL=$(curl -s "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=https://disk.yandex.ru/d/-fiWKh4kzwa66g" | python3 -c "import sys,json; print(json.load(sys.stdin)['href'])")
curl -fSL --retry 3 -o joel-tlou2-jackson.rar "$URL"

# Ellie (Seattle)
URL=$(curl -s "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=https://disk.yandex.ru/d/kAS7GBRC7xSOBw" | python3 -c "import sys,json; print(json.load(sys.stdin)['href'])")
curl -fSL --retry 3 -o ellie-tlou2-seattle.rar "$URL"

# Tess
URL=$(curl -s "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=https://disk.yandex.ru/d/tuf2raTQLizNfw" | python3 -c "import sys,json; print(json.load(sys.stdin)['href'])")
curl -fSL --retry 3 -o tess-tlou-part1.rar "$URL"
```
