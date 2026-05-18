# round-2/normalized/

按 [docs/2-贴图集成进normalized-FBX/PROMPT.md](../../../docs/2-贴图集成进normalized-FBX/PROMPT.md)「产物管理」段，本目录的 `*.fbx` 是**脚本本地 dry-run 残留**，gitignored 不入库。

## 重生成方式

```bash
blender --background --python scripts/blender/wire_textures_into_normalized.py -- \
    --character {joel|ellie|tess}
```

输出：`data/round-2/normalized/{joel|ellie|tess}.fbx`

## 当前状态（spike 失败）

见 [SUMMARY.md](../../../docs/2-贴图集成进normalized-FBX/SUMMARY.md)：脚本能跑通端到端但生成的 FBX 视觉不正确（Blender 4.5 解不出 TLOU 的 DDS 子格式），等外部 DDS 解码方案（如 ImageMagick / Microsoft texconv）落地后重启。

`*.png_cache/` 是 DDS → PNG 转换缓存目录（也 gitignored），spike 失败时未生效。
