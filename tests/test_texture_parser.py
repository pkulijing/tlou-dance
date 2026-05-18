"""
texture_parser 单测 —— 见 docs/2-贴图集成进normalized-FBX/PLAN.md §3.1。

被测函数 parse_part_textures(part_dir, part_name) -> dict[str, Path | None]
  - 扫 part_dir 下的 .dds 文件
  - 返回 {"color": Path|None, "normal": Path|None, "roughness": Path|None, "ao": Path|None}
  - 过滤 _TEST 调试残留 / hex hash dx10 dump / 跨 part 共享贴图
  - 多副本 (1)(2)(3) 取 (1) 或无后缀的最早版本
"""

from pathlib import Path

import pytest
from texture_wiring.texture_parser import (
    detect_dominant_part_prefix,
    parse_part_textures,
)


def _touch(dir_path: Path, *names: str) -> None:
    for n in names:
        (dir_path / n).touch()


def test_parse_all_four_channels(tmp_path: Path) -> None:
    """正常路径：4 通道齐全（Joel/Ellie 风格 .tga(1).dds 后缀）。"""
    _touch(
        tmp_path,
        "joel-body-color.tga(1).dds",
        "joel-body-normal.tga(1).dds",
        "joel-body-roughness.tga(1).dds",
        "joel-body-ao.tga(1).dds",
    )
    result = parse_part_textures(tmp_path, "joel-body")
    assert result["color"] == tmp_path / "joel-body-color.tga(1).dds"
    assert result["normal"] == tmp_path / "joel-body-normal.tga(1).dds"
    assert result["roughness"] == tmp_path / "joel-body-roughness.tga(1).dds"
    assert result["ao"] == tmp_path / "joel-body-ao.tga(1).dds"


def test_parse_partial_channels_returns_none_for_missing(tmp_path: Path) -> None:
    """缺通道：仅 color + normal，roughness/ao 应为 None。"""
    _touch(
        tmp_path,
        "joel-body-color.tga(1).dds",
        "joel-body-normal.tga(1).dds",
    )
    result = parse_part_textures(tmp_path, "joel-body")
    assert result["color"] == tmp_path / "joel-body-color.tga(1).dds"
    assert result["normal"] == tmp_path / "joel-body-normal.tga(1).dds"
    assert result["roughness"] is None
    assert result["ao"] is None


def test_filter_test_suffix_files(tmp_path: Path) -> None:
    """过滤 *_TEST.dds 调试残留。"""
    _touch(
        tmp_path,
        "joel-body-color.tga(1).dds",
        "joel-body-normal.tga(1).dds",
        "joel-body-normal.tga(1)_TEST.dds",  # 应被忽略
    )
    result = parse_part_textures(tmp_path, "joel-body")
    assert result["normal"] == tmp_path / "joel-body-normal.tga(1).dds"
    assert "_TEST" not in str(result["normal"])


def test_filter_hex_hash_dump_files(tmp_path: Path) -> None:
    """过滤 <16hex>_dx10.dds 模型工具 dump 副产物。"""
    _touch(
        tmp_path,
        "joel-body-color.tga(1).dds",
        "joel-body-normal.tga(1).dds",
        "725E5BD2572EE050_dx10.dds",  # 应被忽略
        "50D01799F1051B81_dx10.dds",  # 应被忽略
    )
    result = parse_part_textures(tmp_path, "joel-body")
    assert result["color"] == tmp_path / "joel-body-color.tga(1).dds"
    # hash files don't match channel patterns; assert nothing weird snuck in
    for ch in ("color", "normal", "roughness", "ao"):
        v = result[ch]
        if v is not None:
            assert "_dx10" not in v.name


def test_filter_cross_part_shared_textures(tmp_path: Path) -> None:
    """过滤跨 part 共享 / 泄露贴图（blood/default/fabrics/dina-* 等）。"""
    _touch(
        tmp_path,
        "joel-body-color.tga(1).dds",
        "joel-body-normal.tga(1).dds",
        # 这些都是噪声，不应被当成 joel-body 的贴图
        "blood-color.tga(1).dds",
        "default-flat-normal.tga(1).dds",
        "fabrics-denim-1-normal-ao.tga(1).dds",
        "dina-caruncle-color.tga(1).dds",
        "ellie-brows-ao.tga(1).dds",
    )
    result = parse_part_textures(tmp_path, "joel-body")
    assert result["color"] == tmp_path / "joel-body-color.tga(1).dds"
    assert result["normal"] == tmp_path / "joel-body-normal.tga(1).dds"
    # 这些不属于 joel-body
    assert result["roughness"] is None
    assert result["ao"] is None


def test_dedup_picks_first_download_copy(tmp_path: Path) -> None:
    """多副本：(1) (2) (3) 同时存在时，取 (1)（最早下载）。"""
    _touch(
        tmp_path,
        "joel-body-color.tga(1).dds",
        "joel-body-color.tga(2).dds",
        "joel-body-color.tga(3).dds",
        "joel-body-normal.tga(1).dds",
    )
    result = parse_part_textures(tmp_path, "joel-body")
    assert result["color"] == tmp_path / "joel-body-color.tga(1).dds"


def test_tess_underscore_separator(tmp_path: Path) -> None:
    """Tess 命名风格：分隔符是 `_` 而非 `-`（如 tess_pants_color.dds）。"""
    _touch(
        tmp_path,
        "tess_pants_01_u1_s1_color.dds",
        "tess_pants_01_u1_s1_normal.dds",
        "tess_pants_01_u1_s1_roughness.dds",
        "tess_pants_01_u1_s1_ao.dds",
    )
    result = parse_part_textures(tmp_path, "tess_pants_")
    assert result["color"] == tmp_path / "tess_pants_01_u1_s1_color.dds"
    assert result["normal"] == tmp_path / "tess_pants_01_u1_s1_normal.dds"
    assert result["roughness"] == tmp_path / "tess_pants_01_u1_s1_roughness.dds"
    assert result["ao"] == tmp_path / "tess_pants_01_u1_s1_ao.dds"


def test_normal_does_not_match_normalAO_combined(tmp_path: Path) -> None:
    """*-normalAO.dds 是 normal+AO 合并通道，**不应**被当成 normal（避免误用）。"""
    _touch(
        tmp_path,
        "tess-bkpk-01-color.dds",
        "tess-bkpk-01-normalAO.dds",  # 合并通道，不当成 normal
    )
    result = parse_part_textures(tmp_path, "tess-bkpk")
    assert result["color"] == tmp_path / "tess-bkpk-01-color.dds"
    assert result["normal"] is None  # normalAO ≠ normal


def test_empty_directory_returns_all_none(tmp_path: Path) -> None:
    """空目录：所有通道 None，不抛错。"""
    result = parse_part_textures(tmp_path, "joel-body")
    assert result == {"color": None, "normal": None, "roughness": None, "ao": None}


def test_nonexistent_directory_raises(tmp_path: Path) -> None:
    """目录不存在：抛 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        parse_part_textures(tmp_path / "does_not_exist", "joel-body")


# ============================ detect_dominant_part_prefix ============================


def test_detect_picks_prefix_with_most_channels(tmp_path: Path) -> None:
    """子文件夹内多个前缀混存时，挑覆盖核心通道最多的（模拟 joel-pants/ 实际是 joel-new-pants-* 的情况）。"""
    _touch(
        tmp_path,
        "joel-new-pants-color.tga(1).dds",
        "joel-new-pants-normal.tga(1).dds",
        "joel-new-pants-ao.tga(1).dds",
        "joel-pants-dirt-blend.tga(1).dds",  # 副贴图，不算核心通道
        "blood-normal.tga(1).dds",  # 共享噪声，不带 joel- 前缀（不计）
    )
    assert detect_dominant_part_prefix(tmp_path, "joel") == "joel-new-pants"


def test_detect_handles_multi_segment_middle(tmp_path: Path) -> None:
    """前缀含多段（如 joel-t2-hair-flyaway）也能正确捕获。"""
    _touch(
        tmp_path,
        "joel-beard-color.tga(1).dds",
        "joel-beard-normal.tga(1).dds",
        "joel-beard-roughness.tga(1).dds",
        "joel-beard-ao.tga(1).dds",
        "joel-hair-thin-color.tga(1).dds",
        "joel-hair-thin-normal.tga(1).dds",
    )
    # joel-beard 4 通道 > joel-hair-thin 2 通道
    assert detect_dominant_part_prefix(tmp_path, "joel") == "joel-beard"


def test_detect_returns_none_for_empty_dir(tmp_path: Path) -> None:
    """空目录返回 None，不抛错。"""
    assert detect_dominant_part_prefix(tmp_path, "joel") is None


def test_detect_returns_none_when_no_match(tmp_path: Path) -> None:
    """目录里全是其他角色或共享贴图：返回 None。"""
    _touch(
        tmp_path,
        "blood-normal.tga(1).dds",
        "default-color.tga(1).dds",
        "ellie-brows-color.tga(1).dds",  # 不以 joel- 开头
    )
    assert detect_dominant_part_prefix(tmp_path, "joel") is None


def test_detect_skips_test_and_hex_dump(tmp_path: Path) -> None:
    """_TEST 残留和 hex hash dump 都不计入。"""
    _touch(
        tmp_path,
        "joel-arms-color.tga(1).dds",
        "joel-arms-normal.tga(1).dds",
        "joel-arms-normal.tga(1)_TEST.dds",  # 应被忽略
        "725E5BD2572EE050_dx10.dds",  # 应被忽略
    )
    assert detect_dominant_part_prefix(tmp_path, "joel") == "joel-arms"


def test_detect_nonexistent_dir_returns_none(tmp_path: Path) -> None:
    assert detect_dominant_part_prefix(tmp_path / "missing", "joel") is None
