"""
part_assigner 单测 —— 见 docs/2-贴图集成进normalized-FBX/PLAN.md §3.2。

被测函数 assign_polygons(query_centers, ref_centers, ref_labels) -> list[str]
  对每个 query 多边形中心，找最近的 ref 多边形中心，返回对应标签。

实现层用 numpy chunked brute-force（兼容 Blender 自带 numpy，避免 scipy 依赖）。
"""

import numpy as np
import pytest
from texture_wiring.part_assigner import assign_polygons


def test_two_clusters_separate(tmp_path):
    """正常路径：两个分明的簇，各 query 落到对应 ref。"""
    query = [(0, 0, 0), (10, 10, 10)]
    ref = [(0, 0, 0), (10, 10, 10)]
    labels = ["head", "body"]
    assert assign_polygons(query, ref, labels) == ["head", "body"]


def test_three_clusters_along_axis():
    """3 query 各自落 3 cluster。"""
    query = [(0, 0, 0), (5, 0, 0), (10, 0, 0)]
    ref = [(0, 0, 0), (5, 0, 0), (10, 0, 0)]
    labels = ["a", "b", "c"]
    assert assign_polygons(query, ref, labels) == ["a", "b", "c"]


def test_query_close_to_one_ref():
    """query 偏向某个 ref（避免等距歧义）。"""
    query = [(0.1, 0, 0)]  # 偏向 ref[0]
    ref = [(0, 0, 0), (5, 0, 0)]
    labels = ["a", "b"]
    assert assign_polygons(query, ref, labels) == ["a"]


def test_empty_query_returns_empty():
    """空 query：返回空列表，不抛错。"""
    ref = [(0, 0, 0), (1, 1, 1)]
    labels = ["a", "b"]
    assert assign_polygons([], ref, labels) == []


def test_label_count_mismatch_raises():
    """ref_labels 长度与 ref_centers 不一致：抛 ValueError。"""
    with pytest.raises(ValueError):
        assign_polygons(
            [(0, 0, 0)],
            ref_centers=[(0, 0, 0), (1, 1, 1)],
            ref_labels=["a"],  # 应该是 2 个
        )


def test_empty_ref_raises():
    """没有 ref 供匹配：抛 ValueError（无意义场景）。"""
    with pytest.raises(ValueError):
        assign_polygons([(0, 0, 0)], ref_centers=[], ref_labels=[])


def test_chunking_correctness_on_larger_data():
    """超过 chunk_size 的数据：分块结果应等同一次性计算。"""
    rng = np.random.default_rng(42)
    ref_centers = rng.uniform(-10, 10, size=(100, 3)).tolist()
    ref_labels = [f"part-{i // 25}" for i in range(100)]  # 4 个簇
    query = rng.uniform(-10, 10, size=(2500, 3)).tolist()  # 强迫多次分块

    # 用很小的 chunk_size 触发分块
    result_chunked = assign_polygons(query, ref_centers, ref_labels, chunk_size=100)
    # 跟一次性结果对比
    result_single = assign_polygons(query, ref_centers, ref_labels, chunk_size=10_000)
    assert result_chunked == result_single


def test_returns_list_of_strings():
    """返回值类型必须是 list[str]，不是 numpy.ndarray 等。"""
    result = assign_polygons([(0, 0, 0)], [(0, 0, 0)], ["x"])
    assert isinstance(result, list)
    assert all(isinstance(label, str) for label in result)
