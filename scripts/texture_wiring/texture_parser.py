"""
扫描部件 Textures 目录，识别 PBR 4 通道（color/normal/roughness/ao）的 .dds 路径。

规则细节见 docs/2-贴图集成进normalized-FBX/PLAN.md §1.4 / §3.1。
"""

import re
from pathlib import Path

_CHANNELS = ("color", "normal", "roughness", "ao")

# 噪声文件过滤
_TEST_SUFFIX = re.compile(r"_TEST", re.IGNORECASE)
_HEX_HASH_DUMP = re.compile(r"^[0-9A-F]{16}_dx10\.dds$", re.IGNORECASE)

# 多副本下载后缀 `(N)` 的捕获
_DL_COUNTER = re.compile(r"\((\d+)\)")


def parse_part_textures(part_dir: Path, part_name: str) -> dict[str, Path | None]:
    """
    返回 {"color": Path|None, "normal": Path|None, "roughness": Path|None, "ao": Path|None}。

    part_name 是部件前缀（如 "joel-body" / "tess_pants_" / "tess-head"）。结尾的 `_`/`-` 会被去掉。
    分隔符 `_` 与 `-` 同等处理（Tess 用下划线）。
    """
    if not part_dir.is_dir():
        raise FileNotFoundError(f"part directory not found: {part_dir}")

    prefix = re.escape(part_name.rstrip("-_"))
    sep = r"[-_]"
    # 中间允许任意层级（如 tess-head-01-u1-s1-）的 [\w-]+ 段，必须以分隔符结尾
    middle = rf"(?:[\w\-]+{sep})?"
    channel_re = {
        ch: re.compile(rf"^{prefix}{sep}{middle}{ch}(?:{sep}|\.|$)", re.IGNORECASE)
        for ch in _CHANNELS
    }

    # 收集所有 .dds 候选并过滤噪声
    candidates = [
        f
        for f in part_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() == ".dds"
        and not _TEST_SUFFIX.search(f.name)
        and not _HEX_HASH_DUMP.match(f.name)
    ]

    result: dict[str, Path | None] = dict.fromkeys(_CHANNELS)
    for ch in _CHANNELS:
        matches = [f for f in candidates if channel_re[ch].match(f.name)]
        if matches:
            matches.sort(key=_dedup_priority)
            result[ch] = matches[0]
    return result


def _dedup_priority(p: Path) -> tuple[int, int, str]:
    """
    排序键：无 `(N)` 后缀的文件优先（视为最早版本），其次按 N 升序，最后按文件名稳定。
    """
    m = _DL_COUNTER.search(p.name)
    if m is None:
        return (0, 0, p.name)
    return (1, int(m.group(1)), p.name)


def detect_dominant_part_prefix(part_dir: Path, character_prefix: str) -> str | None:
    """
    扫 part_dir 找以 `<character_prefix>-` 开头、覆盖最多核心通道（color/normal/roughness/ao）
    的"实际贴图前缀"。

    用例：游戏 raw 资产里子文件夹名（mesh 导出部件名）跟内部贴图文件前缀（美术工作流命名）
    不一致 —— 如 Joel 的 `Textures/joel-body/` 里实际全是 `joel-arms-*` 文件。

    返回 None：找不到任何覆盖核心通道的前缀。

    规则：
      - 只看 `<character_prefix>-...` 开头的 .dds 文件，过滤 _TEST / hex dump
      - 提取 `<prefix>-<channel>` 的前缀部分（贪婪非贪婪平衡），按通道覆盖数排序
      - 同覆盖数取最短前缀（更通用），再字典序
    """
    if not part_dir.is_dir():
        return None

    pattern = re.compile(
        rf"^({re.escape(character_prefix)}-[\w-]+?)-(color|normal|roughness|ao)(?:[-_]|\.)",
        re.IGNORECASE,
    )

    counts: dict[str, set[str]] = {}
    for f in part_dir.iterdir():
        if not (f.is_file() and f.suffix.lower() == ".dds"):
            continue
        if _TEST_SUFFIX.search(f.name) or _HEX_HASH_DUMP.match(f.name):
            continue
        m = pattern.match(f.name)
        if m:
            prefix = m.group(1).lower()
            channel = m.group(2).lower()
            counts.setdefault(prefix, set()).add(channel)

    if not counts:
        return None

    return max(counts, key=lambda p: (len(counts[p]), -len(p), p))
