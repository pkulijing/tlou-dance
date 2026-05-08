"""
Blender headless inspector for round-0 模型可行性验证。

用法：
    blender --background --python inspect_model.py -- <input-file> [<extra-fbx>...]

支持 .blend 与 .fbx；多个 .fbx 会合并到同一场景再统计。
输出每个 mesh 的顶点/面数、armature 骨骼数与 sample bones、material 列表、
缺失贴图清单 —— 用以判定 Phase 1 三项验收（几何 / 骨骼 / 贴图）是否通过。
"""

import sys
from pathlib import Path

import bpy

ARGV = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []

if not ARGV:
    raise SystemExit(
        "usage: blender --background --python inspect_model.py -- <input-file> [<extra-fbx>...]"
    )


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path: Path) -> None:
    if path.suffix.lower() == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path))
    elif path.suffix.lower() == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        raise SystemExit(f"unsupported extension: {path.suffix}")


def report() -> None:
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]

    print(f"\n=== mesh objects: {len(meshes)} ===")
    total_v = total_f = 0
    for m in meshes:
        v = len(m.data.vertices)
        f = len(m.data.polygons)
        total_v += v
        total_f += f
        print(f"  - {m.name}: verts={v} faces={f}")
    print(f"  TOTAL: verts={total_v} faces={total_f}")

    print(f"\n=== armatures: {len(armatures)} ===")
    for a in armatures:
        bones = a.data.bones
        print(f"  - {a.name}: bones={len(bones)}")
        sample = [b.name for b in bones[:12]]
        print(f"    sample: {sample}")

    print(f"\n=== materials: {len(bpy.data.materials)} ===")
    for mat in bpy.data.materials[:15]:
        print(f"  - {mat.name}")

    images = list(bpy.data.images)
    print(f"\n=== images (textures): {len(images)} ===")
    missing = [
        img
        for img in images
        if img.source == "FILE"
        and img.filepath
        and not Path(bpy.path.abspath(img.filepath)).exists()
    ]
    print(f"  missing on disk: {len(missing)}")
    for img in missing[:8]:
        print(f"    - {img.name} -> {img.filepath}")


reset_scene()
inputs = [Path(p).resolve() for p in ARGV]
print(f"=== INSPECT: {len(inputs)} file(s) ===")
for p in inputs:
    print(f"  loading: {p}")
    load(p)
report()
