"""
两类别名映射（来源见 docs/2-贴图集成进normalized-FBX/PLAN.md §1.1, §1.3）：

1. tess_mesh_to_part_prefix —— Tess 单 FBX 内 27 个 submesh 的 object 名 → 贴图前缀
   原因：Tess raw 是 1 FBX 多 mesh，object 名前缀（"head_..."、"backpack_..."）跟 Textures/
   平铺文件的命名（"tess-head-..."、"tess-bkpk-..."）不是字面对应，需查表。

2. resolve_cloth_parent —— cloth-sim 附件部件名 → 父部件名
   原因：游戏引擎里 cloth helper 没独立美术资源，运行时用 parent 部件材质（背包带 = 背包同材质）。
   raw 提取没单独导贴图。这张表硬编码 Joel/Ellie 实际数据。
"""

# Tess submesh 前缀（mesh 名 `_` 之前的部分）→ 贴图文件名前缀
# 贴图前缀不带尾部分隔符，由 texture_parser 自己处理（其 rstrip("-_") 已正确）
_TESS_MESH_PREFIX_TO_TEXTURE_PREFIX: dict[str, str] = {
    "backpack": "tess-bkpk",
    "boots": "tess-boot",
    "head": "tess-head",
    "pants": "tess_pants",
    "shirt": "tess_shirt",
    "hair": "tess_hair",
    "scarf": "tess-scarf",
    "eyeballs": "tess-eyes",
    "tanktop": "marlene-tanktop",  # Tess 用了 Marlene 角色的 tanktop 贴图（共享资产）
    "teeth": "u-teeth",
    "saliva": "u-saliva",
    "tear": "tear",
}


def tess_mesh_to_part_prefix(mesh_name: str) -> str | None:
    """从 Tess submesh 的 object 名（如 'head_tess_head_01_*'）取下划线前的前缀，查表得贴图前缀。"""
    if not mesh_name:
        return None
    head = mesh_name.split("_", 1)[0]
    return _TESS_MESH_PREFIX_TO_TEXTURE_PREFIX.get(head)


# cloth-sim 附件 → 提供材质的父部件
# Ellie 没有 ellie-jacket 主材质，jacket-cloth 回退到 ellie-body
_CLOTH_PARENT_MAP: dict[str, str] = {
    "joel-backpack-strap-cloth": "joel-backpack",
    "joel-backpack-jacket-cloth": "joel-backpack",
    "ellie-bandage-forearm-cloth": "ellie-bandage",
    "ellie-backpack-zip-cloth": "ellie-backpack",
    "ellie-jacket-cloth": "ellie-body",
    "ellie-strand-hair-cloth": "ellie-hair-cloth",
}


def resolve_cloth_parent(part_name: str) -> str | None:
    """登记过的 cloth 附件返回父部件名；非 cloth 或未登记返回 None。"""
    return _CLOTH_PARENT_MAP.get(part_name)
