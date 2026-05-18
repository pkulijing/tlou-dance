"""
alias 模块单测 —— 见 docs/2-贴图集成进normalized-FBX/PLAN.md §3.3, §3.4。

被测函数：
  - tess_mesh_to_part_prefix(mesh_name) -> str | None
    把 Tess 单 FBX 内部 27 个 submesh 的 object 名映射到贴图前缀。
  - resolve_cloth_parent(part_name) -> str | None
    把 cloth-sim 附件部件名映射到能提供材质的父部件名（用 Joel/Ellie 的实际数据硬编码）。
"""

from texture_wiring.alias import resolve_cloth_parent, tess_mesh_to_part_prefix

# ============================ tess_mesh_to_part_prefix ============================


def test_tess_head_mesh_to_prefix():
    assert (
        tess_mesh_to_part_prefix("head_tess_head_01_u1_g1_LODShape0_shader2_merged_partition0")
        == "tess-head"
    )


def test_tess_pants_mesh_to_prefix():
    assert (
        tess_mesh_to_part_prefix("pants_tess_pnt_01_u1_g1_LODShape0_shader1_merged_partition0")
        == "tess_pants"
    )


def test_tess_shirt_mesh_to_prefix():
    assert (
        tess_mesh_to_part_prefix("shirt_tess_shirt_01_u1_g1_LODShape0_shader0_merged_partition0")
        == "tess_shirt"
    )


def test_tess_backpack_mesh_to_prefix():
    assert (
        tess_mesh_to_part_prefix("backpack_tess_bkpk_01_u1_g1_LODShape0_shader0_merged_partition2")
        == "tess-bkpk"
    )


def test_tess_boots_mesh_to_prefix():
    assert (
        tess_mesh_to_part_prefix("boots_tess_boot_01_u1_g1_LODShape0_shader0_merged_partition0")
        == "tess-boot"
    )


def test_tess_hair_mesh_to_prefix():
    assert (
        tess_mesh_to_part_prefix("hair_tess_hair_01_u1_g1_lod0_LODShape0_shader2_merged_p_976d63c")
        == "tess_hair"
    )


def test_tess_scarf_mesh_to_prefix():
    """注意：scarf mesh 来自 hair lodshape，但应映射到 scarf 贴图前缀。"""
    assert (
        tess_mesh_to_part_prefix("scarf_tess_hair_01_u1_g1_lod0_LODShape0_shader0_merged__12279f3")
        == "tess-scarf"
    )


def test_tess_eyeballs_mesh_to_prefix():
    assert (
        tess_mesh_to_part_prefix("eyeballs_tess_head_01_u1_g1_LODShape0_shader3_merged_partition0")
        == "tess-eyes"
    )


def test_tess_unknown_mesh_returns_none():
    """未知前缀：返回 None，调用方决定 fallback 策略。"""
    assert tess_mesh_to_part_prefix("foobar_tess_unknown_xyz") is None
    assert tess_mesh_to_part_prefix("") is None


# ============================ resolve_cloth_parent ============================


def test_joel_backpack_strap_cloth_inherits_backpack():
    assert resolve_cloth_parent("joel-backpack-strap-cloth") == "joel-backpack"


def test_joel_backpack_jacket_cloth_inherits_backpack():
    """Joel 的背包夹克布料附件也归到 backpack 主材质。"""
    assert resolve_cloth_parent("joel-backpack-jacket-cloth") == "joel-backpack"


def test_ellie_bandage_forearm_cloth_inherits_bandage():
    assert resolve_cloth_parent("ellie-bandage-forearm-cloth") == "ellie-bandage"


def test_ellie_backpack_zip_cloth_inherits_backpack():
    assert resolve_cloth_parent("ellie-backpack-zip-cloth") == "ellie-backpack"


def test_ellie_jacket_cloth_falls_back_to_body():
    """Ellie 没有 ellie-jacket 主材质，jacket-cloth 回退到 ellie-body。"""
    assert resolve_cloth_parent("ellie-jacket-cloth") == "ellie-body"


def test_ellie_strand_hair_cloth_inherits_hair_cloth():
    """ellie-strand-hair-cloth 归到 ellie-hair-cloth（注意父也带 cloth 后缀）。"""
    assert resolve_cloth_parent("ellie-strand-hair-cloth") == "ellie-hair-cloth"


def test_non_cloth_part_returns_none():
    """非 cloth 部件（即主材质本身）：返回 None。"""
    assert resolve_cloth_parent("joel-body") is None
    assert resolve_cloth_parent("ellie-head") is None


def test_unknown_cloth_part_returns_none():
    """未登记的 cloth 部件：返回 None（让调用方记日志兜底）。"""
    assert resolve_cloth_parent("unknown-cloth") is None
