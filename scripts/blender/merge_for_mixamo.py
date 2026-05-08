"""
Phase 1 — 把一个角色的多 FBX 部件合并成「适合上 Mixamo Auto-Rigger」的单 mesh FBX。

为什么剥离骨骼：ND 原骨骼（`spinea/spineb/heada/.../l_eyeball...`）不符合 HIK/Biped 命名约定，
Mixamo 自动映射几乎一定失败。Adobe 官方文档建议这种情况直接传**无骨骼**网格，让 Mixamo
auto-rig 自己生成 mixamorig:* 标准骨骼。

为什么 join 成单 mesh：Mixamo 上传支持 FBX/OBJ/ZIP，但单 mesh 处理最稳；多 object
会让标记定位（手腕、肘、膝、裆）算法困惑。

用法：
    blender --background --python merge_for_mixamo.py -- \
        <character_name> <output_dir> <input1.fbx> [<input2.fbx> ...]

输出：
    <output_dir>/<character_name>-merged.blend     —— 含 mesh-only 场景，方便 Blender GUI 验证
    <output_dir>/<character_name>-for-mixamo.fbx   —— mesh-only，给 Mixamo 上传

注意：
- 强制重置场景，避免拿到上一次运行的残留 datablocks
- 用「import 前后 bpy.data.objects 集合差」追踪新导入对象，不依赖 Blender 默认选中行为
- Apply 所有 transform（位置/旋转/缩放）→ 确保导出 FBX 在 Mixamo 是 (0,0,0) 起点
"""

import sys
from pathlib import Path

import bpy

ARGV = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(ARGV) < 3:
    raise SystemExit(
        "usage: blender --background --python merge_for_mixamo.py -- "
        "<character_name> <output_dir> <input1.fbx> [<input2.fbx> ...]"
    )

CHARACTER, OUT_DIR, *INPUTS = ARGV
OUT_DIR_PATH = Path(OUT_DIR).resolve()
OUT_DIR_PATH.mkdir(parents=True, exist_ok=True)

print(f"=== merge_for_mixamo: {CHARACTER} ({len(INPUTS)} parts) ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

for inp in INPUTS:
    inp_path = Path(inp).resolve()
    if not inp_path.exists():
        raise SystemExit(f"input not found: {inp_path}")
    before = set(bpy.data.objects)
    print(f"  importing {inp_path.name}")
    bpy.ops.import_scene.fbx(filepath=str(inp_path))
    new_objs = set(bpy.data.objects) - before
    print(f"    +{len(new_objs)} objects")

mesh_objects = [o for o in bpy.data.objects if o.type == "MESH"]
armature_objects = [o for o in bpy.data.objects if o.type == "ARMATURE"]
print(f"\n=== before strip: {len(mesh_objects)} meshes, {len(armature_objects)} armatures ===")

if not mesh_objects:
    raise SystemExit("no mesh objects found after import — aborting")


def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    if objs:
        bpy.context.view_layer.objects.active = objs[0]


# 1) 移除所有 mesh 的 armature modifier（mesh 落到 bind pose 顶点位置）
for m in mesh_objects:
    for mod in [mm for mm in m.modifiers if mm.type == "ARMATURE"]:
        m.modifiers.remove(mod)

# 2) 把 mesh 从 armature parent 解绑（保留 world transform）
for m in mesh_objects:
    if m.parent and m.parent.type == "ARMATURE":
        select_only([m])
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")

# 3) 删除所有 armature
select_only(armature_objects)
if armature_objects:
    bpy.ops.object.delete()
print(f"removed {len(armature_objects)} armatures")

# 4) Apply 所有 transform，确保在世界 (0,0,0) 朝 +Z
mesh_objects = [o for o in bpy.data.objects if o.type == "MESH"]
select_only(mesh_objects)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 5) Join 成单 mesh
select_only(mesh_objects)
bpy.ops.object.join()
joined = bpy.context.active_object
joined.name = CHARACTER
print(
    f"joined into: {joined.name}, verts={len(joined.data.vertices)}, faces={len(joined.data.polygons)}"
)

# 6) 保存 .blend 供 GUI 验证
blend_out = OUT_DIR_PATH / f"{CHARACTER}-merged.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_out))
print(f"saved blend: {blend_out}")

# 7) 导 FBX（mesh-only，无 armature，无嵌入贴图，给 Mixamo）
fbx_out = OUT_DIR_PATH / f"{CHARACTER}-for-mixamo.fbx"
select_only([joined])
bpy.ops.export_scene.fbx(
    filepath=str(fbx_out),
    use_selection=True,
    object_types={"MESH"},
    add_leaf_bones=False,
    bake_anim=False,
    embed_textures=False,
)

fbx_size_mb = fbx_out.stat().st_size / 1024 / 1024
print(f"exported: {fbx_out} ({fbx_size_mb:.1f} MB)")
if fbx_size_mb > 30:
    print("  ⚠️  超过 Mixamo 30MB 上限，需要 Decimate 减面（修脚本加 decimate modifier）")
else:
    print("  ✓ 在 Mixamo 30MB 限制内")
