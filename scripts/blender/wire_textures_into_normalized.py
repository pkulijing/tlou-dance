"""
Round 2 — 把 raw 部件 mesh 当作"标签参考点云"，KD-tree match normalized FBX 的多边形 →
按部件赋 PBR 4 通道材质（Color/Normal/Roughness/AO）→ 导出 FBX with embed_textures。

法线默认翻 Y（DirectX → OpenGL）；详见 docs/2-贴图集成进normalized-FBX/PLAN.md §2.4。

用法：
    blender --background --python scripts/blender/wire_textures_into_normalized.py -- \
        --character {joel|ellie|tess} [--out-dir data/round-2/normalized/]

输出：
    <out_dir>/<character>.fbx  —— gitignored，本地 dry-run 验证用
"""

import argparse
import sys
from pathlib import Path

import bpy

# 让 pure-logic 模块（scripts/texture_wiring/）能被 import
SCRIPT_DIR = Path(__file__).resolve().parent  # scripts/blender/
sys.path.insert(0, str(SCRIPT_DIR.parent))  # scripts/

from texture_wiring.alias import resolve_cloth_parent, tess_mesh_to_part_prefix  # noqa: E402
from texture_wiring.part_assigner import assign_polygons  # noqa: E402
from texture_wiring.texture_parser import (  # noqa: E402
    detect_dominant_part_prefix,
    parse_part_textures,
)

PROJECT_ROOT = SCRIPT_DIR.parent.parent  # tlou-dance/

CHAR_CONFIG = {
    "joel": {
        "normalized": PROJECT_ROOT / "data/round-0/normalized/joel.fbx",
        "raw_root": PROJECT_ROOT / "data/round-0/raw/joel/TLOU2 - Joel (Jackson)",
        "kind": "multi-fbx",
    },
    "ellie": {
        "normalized": PROJECT_ROOT / "data/round-0/normalized/ellie.fbx",
        "raw_root": PROJECT_ROOT / "data/round-0/raw/ellie/TLOU2 - Ellie (Seattle)",
        "kind": "multi-fbx",
    },
    "tess": {
        "normalized": PROJECT_ROOT / "data/round-0/normalized/tess.fbx",
        "raw_root": PROJECT_ROOT / "data/round-0/raw/tess/TLOU Part1 - Tess",
        "kind": "single-fbx",
        "single_fbx_name": "tess.mesh.fbx",
    },
}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--character", choices=list(CHAR_CONFIG), required=True)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=PROJECT_ROOT / "data/round-2/normalized",
    )
    return p.parse_args(argv)


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_fbx(path: Path) -> set:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path))
    return set(bpy.data.objects) - before


def compute_polygon_centers(mesh_obj) -> list[tuple[float, float, float]]:
    """每个 polygon 在世界坐标系下的中心。"""
    mw = mesh_obj.matrix_world
    out = []
    for poly in mesh_obj.data.polygons:
        wc = mw @ poly.center
        out.append((wc.x, wc.y, wc.z))
    return out


def build_part_reference(character: str, raw_root: Path) -> tuple[list, list]:
    """
    返回 (ref_centers, ref_labels) —— 三人统一的"带标签参考点云"。

    Joel/Ellie: 多 FBX，标签 = filename stem（如 'joel-body'）
    Tess: 单 FBX 内 27 个 mesh，标签 = tess_mesh_to_part_prefix(object name)
    """
    ref_centers: list[tuple[float, float, float]] = []
    ref_labels: list[str] = []

    cfg = CHAR_CONFIG[character]
    if cfg["kind"] == "single-fbx":
        single_fbx = raw_root / cfg["single_fbx_name"]
        new_objs = import_fbx(single_fbx)
        unknown_meshes = []
        for obj in new_objs:
            if obj.type != "MESH":
                continue
            prefix = tess_mesh_to_part_prefix(obj.name)
            if prefix is None:
                unknown_meshes.append(obj.name)
                prefix = "tess-head"  # fallback
            centers = compute_polygon_centers(obj)
            ref_centers.extend(centers)
            ref_labels.extend([prefix] * len(centers))
        if unknown_meshes:
            print(
                f"  warn: {len(unknown_meshes)} Tess submeshes 用 fallback 'tess-head'："
                f" {unknown_meshes[:5]}{'...' if len(unknown_meshes) > 5 else ''}"
            )
    else:
        # Joel/Ellie: multi-fbx
        fbx_files = sorted(raw_root.glob("*.fbx"))
        for fbx in fbx_files:
            new_objs = import_fbx(fbx)
            part_label = fbx.stem
            for obj in new_objs:
                if obj.type != "MESH":
                    continue
                centers = compute_polygon_centers(obj)
                ref_centers.extend(centers)
                ref_labels.extend([part_label] * len(centers))

    return ref_centers, ref_labels


def _ensure_png(src_dds, cache_dir: Path):
    """
    DDS → PNG 预转换：原 DDS 在 Blender 4.5 里时常懒解码 / 子格式不认，最终 FBX embed 后
    可能在 viewport 里读不到像素（roughness 全黑 = 镜面 = 镀铬效果；color 全黑 = 灰）。

    先用 Blender 把 DDS 转成 PNG（PNG 解码最稳），再喂给材质，FBX embed 出来的也是 PNG。
    这样从 raw 资产到最终用户 import 全程贴图都能正确解码。

    返回 PNG 路径；转不出来则返回 None（caller 跳过该通道，由 BSDF 默认值兜底）。
    """
    if src_dds is None:
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    png_path = cache_dir / f"{src_dds.stem}.png"
    if png_path.exists() and png_path.stat().st_size > 0:
        return png_path

    img = bpy.data.images.load(str(src_dds))
    img.filepath_raw = str(png_path)
    img.file_format = "PNG"
    try:
        img.save()
    except RuntimeError as e:
        print(f"      [PNG 转换失败] {src_dds.name}: {e}")
        bpy.data.images.remove(img)
        return None
    bpy.data.images.remove(img)
    if png_path.exists() and png_path.stat().st_size > 0:
        return png_path
    return None


def _load_png(png_path, non_color: bool = False):
    if png_path is None:
        return None
    img = bpy.data.images.load(str(png_path), check_existing=True)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def build_pbr_material(name: str, color, normal, roughness, ao, png_cache: Path):
    """
    构造 Principled BSDF + 直连贴图节点链。

    Shader 图刻意保持"Image Texture → BSDF socket"的最简模式：Blender FBX 导出器只能跟踪
    这种直连，遇到中间节点（Mix / Separate-Combine）就丢图。AO 多叠 + 法线 G 翻转因此放弃，
    留为后续轮优化（参见 SUMMARY 局限性段）。

    所有 DDS 先经 _ensure_png 预转换为 PNG，避免最终 FBX 内嵌后在 viewport 解码失败。
    转不出的通道由 Principled BSDF 默认值兜底。
    """
    color_png = _ensure_png(color, png_cache)
    normal_png = _ensure_png(normal, png_cache)
    roughness_png = _ensure_png(roughness, png_cache)

    color_img = _load_png(color_png)
    normal_img = _load_png(normal_png, non_color=True)
    roughness_img = _load_png(roughness_png, non_color=True)

    skipped = []
    if color and color_img is None:
        skipped.append("color")
    if normal and normal_img is None:
        skipped.append("normal")
    if roughness and roughness_img is None:
        skipped.append("roughness")
    if skipped:
        print(f"      [{name}] PNG 转换失败，跳过通道：{skipped}")

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    for n in list(nodes):
        nodes.remove(n)

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    if color_img is not None:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = color_img
        tex.location = (-500, 300)
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if normal_img is not None:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = normal_img
        tex.location = (-500, 0)
        nmap = nodes.new("ShaderNodeNormalMap")
        nmap.location = (-200, 0)
        links.new(tex.outputs["Color"], nmap.inputs["Color"])
        links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    if roughness_img is not None:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = roughness_img
        tex.location = (-500, -300)
        links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])

    # ao: 本轮放弃（详见 SUMMARY 局限性段）

    return mat


def main() -> None:
    args = parse_args()
    cfg = CHAR_CONFIG[args.character]
    print(f"\n=== wire_textures: {args.character} ===")
    print(f"  normalized: {cfg['normalized']}")
    print(f"  raw_root:   {cfg['raw_root']}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    reset_scene()

    # 1) import normalized FBX, locate joined mesh + armature
    norm_objs = import_fbx(cfg["normalized"])
    norm_meshes = [o for o in norm_objs if o.type == "MESH"]
    if len(norm_meshes) != 1:
        raise SystemExit(f"expected 1 mesh in normalized FBX, got {len(norm_meshes)}")
    norm_mesh = norm_meshes[0]
    norm_armature = (
        norm_mesh.parent if norm_mesh.parent and norm_mesh.parent.type == "ARMATURE" else None
    )
    print(f"  normalized mesh: {norm_mesh.name}, polys={len(norm_mesh.data.polygons)}")

    # 2) import raw 部件 → ref 点云
    print("  importing raw parts ...")
    ref_centers, ref_labels = build_part_reference(args.character, cfg["raw_root"])
    unique_ref_parts = sorted(set(ref_labels))
    print(f"  ref centers={len(ref_centers)}, unique parts={len(unique_ref_parts)}")
    print(f"  parts: {unique_ref_parts}")

    # 3) KD-tree match
    query_centers = compute_polygon_centers(norm_mesh)
    print(f"  matching {len(query_centers)} polygons against {len(ref_centers)} refs ...")
    poly_labels = assign_polygons(query_centers, ref_centers, ref_labels)
    assigned_parts = sorted(set(poly_labels))
    print(f"  assigned parts on normalized mesh: {assigned_parts}")

    # 4) 删除所有 ref objects（保留 norm_mesh + armature）
    keep = {norm_mesh}
    if norm_armature:
        keep.add(norm_armature)
    for o in list(bpy.data.objects):
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)

    # 5) 为每个 unique part 建材质（cloth → 父部件合并 slot）
    textures_root = cfg["raw_root"] / "Textures"
    png_cache = args.out_dir / f"{args.character}.png_cache"
    effective_to_slot: dict[str, int] = {}
    part_to_slot: dict[str, int] = {}
    for part in assigned_parts:
        effective = resolve_cloth_parent(part) or part
        if effective not in effective_to_slot:
            if cfg["kind"] == "single-fbx":
                # Tess: 平铺 textures/
                channels = parse_part_textures(textures_root, effective)
            else:
                # Joel/Ellie: 子文件夹
                part_dir = textures_root / effective
                if part_dir.is_dir():
                    # 先按字面前缀匹配
                    channels = parse_part_textures(part_dir, effective)
                    # 全 None：fallback 到自动探测主贴图前缀（处理 folder ≠ file 前缀的情况）
                    if all(v is None for v in channels.values()):
                        char_prefix = args.character  # joel / ellie
                        detected = detect_dominant_part_prefix(part_dir, char_prefix)
                        if detected:
                            print(f"    auto-detected '{detected}' for folder '{effective}'")
                            channels = parse_part_textures(part_dir, detected)
                else:
                    print(f"    warn: no textures dir for '{effective}', skipping")
                    channels = dict.fromkeys(("color", "normal", "roughness", "ao"))
            ch_status = {k: ("✓" if v else "·") for k, v in channels.items()}
            print(
                f"    {effective}: color={ch_status['color']} normal={ch_status['normal']} rough={ch_status['roughness']} ao={ch_status['ao']}"
            )
            mat = build_pbr_material(effective, **channels, png_cache=png_cache)
            slot_idx = len(norm_mesh.data.materials)
            norm_mesh.data.materials.append(mat)
            effective_to_slot[effective] = slot_idx
        part_to_slot[part] = effective_to_slot[effective]

    # 6) 设 polygon.material_index
    for i, poly in enumerate(norm_mesh.data.polygons):
        poly.material_index = part_to_slot[poly_labels[i]]
    print(
        f"  built {len(effective_to_slot)} materials, assigned to {len(norm_mesh.data.polygons)} polygons"
    )

    # 7) export FBX with embedded textures
    bpy.ops.object.select_all(action="DESELECT")
    norm_mesh.select_set(True)
    if norm_armature:
        norm_armature.select_set(True)
    out_path = args.out_dir / f"{args.character}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(out_path),
        use_selection=True,
        embed_textures=True,
        path_mode="COPY",
        bake_anim=False,
        add_leaf_bones=False,
    )
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\n=== exported {out_path} ({size_mb:.1f} MB) ===")


if __name__ == "__main__":
    main()
