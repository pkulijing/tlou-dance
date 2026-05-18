"""
对 query 多边形中心找最近的 ref 多边形中心，返回对应部件标签。

实现：numpy 分块 brute-force（chunked）。避开 scipy 依赖（Blender 自带 numpy 不带 scipy）。
对 N(query)×M(ref) 数据，按 chunk_size 切 query 后做矩阵广播 argmin，峰值内存 O(chunk_size × M)。
"""

import numpy as np

DEFAULT_CHUNK = 1024


def assign_polygons(
    query_centers: list[tuple[float, float, float]],
    ref_centers: list[tuple[float, float, float]],
    ref_labels: list[str],
    chunk_size: int = DEFAULT_CHUNK,
) -> list[str]:
    if len(ref_centers) != len(ref_labels):
        raise ValueError(
            f"ref_centers ({len(ref_centers)}) 与 ref_labels ({len(ref_labels)}) 长度不一致"
        )
    if len(ref_centers) == 0:
        raise ValueError("ref_centers 为空，无法进行最近邻匹配")
    if len(query_centers) == 0:
        return []

    qc = np.asarray(query_centers, dtype=np.float64)  # (N, 3)
    rc = np.asarray(ref_centers, dtype=np.float64)  # (M, 3)

    out: list[str] = []
    for start in range(0, len(qc), chunk_size):
        chunk = qc[start : start + chunk_size]  # (k, 3)
        # 平方距离矩阵 (k, M)
        d2 = ((chunk[:, None, :] - rc[None, :, :]) ** 2).sum(axis=-1)
        nearest = d2.argmin(axis=1)  # (k,)
        out.extend(ref_labels[i] for i in nearest)

    return out
