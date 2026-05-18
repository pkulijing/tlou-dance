"""阶段 0：从源视频切 10s 片段（friendly / hard）。

时间码解析（parse_timecode）按 Constitution TDD：先测后写。
ffmpeg 切片走系统 ffmpeg 子进程（外部系统集成，按 TDD 例外处理，仅 smoke 验证）。

CLI 用法::

    uv run python -m round1_motion.prepare_clip \
        --input data/round1_motion/raw/source.mp4 \
        --start 01:23:00 \
        --end 01:23:10 \
        --output data/round1_motion/clip/friendly_10s.mp4
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_timecode(tc: str) -> float:
    """Parse a timecode string into seconds.

    Accepted forms:
    - ``HH:MM:SS`` / ``HH:MM:SS.mmm``
    - ``MM:SS``   / ``MM:SS.mmm``
    - ``SS``      / ``SS.mmm``

    范围检查仅在多段输入时生效（即只有"01:60:00" 这种**带冒号**的形式
    才会因 m/s ≥ 60 报错；纯秒数如 "90" 不会报错）。

    Raises:
        TypeError: 非字符串输入
        ValueError: 空 / 格式不合法 / 段内非数字 / 负数 / 多段时 m/s ≥ 60
    """
    if not isinstance(tc, str):
        raise TypeError(f"timecode must be str, got {type(tc).__name__}")
    stripped = tc.strip()
    if not stripped:
        raise ValueError("empty timecode")
    parts = stripped.split(":")
    parts_count = len(parts)
    if parts_count > 3 or any(p == "" for p in parts):
        raise ValueError(f"invalid timecode format: {tc!r}")
    try:
        nums = [float(p) for p in parts]
    except ValueError as e:
        raise ValueError(f"non-numeric timecode parts in {tc!r}") from e
    if any(n < 0 for n in nums):
        raise ValueError(f"negative timecode: {tc!r}")
    while len(nums) < 3:
        nums.insert(0, 0)
    h, m, s = nums
    if parts_count >= 2 and s >= 60:
        raise ValueError(f"seconds field >= 60 in {tc!r}")
    if parts_count >= 3 and m >= 60:
        raise ValueError(f"minutes field >= 60 in {tc!r}")
    return h * 3600 + m * 60 + s


def cut_clip(
    input_path: Path,
    start_sec: float,
    end_sec: float,
    output_path: Path,
    *,
    stream_copy: bool = False,
) -> None:
    """用系统 ffmpeg 切 [start_sec, end_sec] 这一段。

    stream_copy=True 时走 -c copy（秒级，但只能对齐到关键帧，适合"切尾巴"这类粗切）；
    False 时走 libx264 re-encode（精确帧对齐，适合 friendly 10s 精切）。
    """
    duration = end_sec - start_sec
    if duration <= 0:
        raise ValueError(f"end ({end_sec}) must be > start ({start_sec})")
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if stream_copy:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start_sec:.3f}",
            "-i",
            str(input_path),
            "-t",
            f"{duration:.3f}",
            "-c",
            "copy",
            str(output_path),
        ]
    else:
        # 双重 seek：先 input-side 粗 seek 到 start 前 1s（解码前对齐 keyframe），
        # 再 output-side 微调 1s 到精确起点。等价于"先粗后精"，起点仍精确到帧。
        # 单纯 output-side seek（-ss 放 -i 之后）配合 libx264 在某些 1080p h264
        # 输入上会触发 SIGSEGV，双重 seek 路径绕开该 bug，且 ffmpeg 官方推荐。
        coarse_offset = min(start_sec, 1.0)
        coarse_seek = start_sec - coarse_offset
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{coarse_seek:.3f}",
            "-i",
            str(input_path),
            "-ss",
            f"{coarse_offset:.3f}",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-avoid_negative_ts",
            "make_zero",
            str(output_path),
        ]
    subprocess.run(cmd, check=True)


def _check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not found on PATH; install ffmpeg first")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Cut a clip from a source video by timecodes.")
    p.add_argument("--input", required=True, type=Path, help="Source video path")
    p.add_argument("--start", required=True, type=str, help="Start timecode (HH:MM:SS[.mmm])")
    p.add_argument("--end", required=True, type=str, help="End timecode (HH:MM:SS[.mmm])")
    p.add_argument("--output", required=True, type=Path, help="Output clip path")
    p.add_argument(
        "--copy",
        action="store_true",
        help="Use ffmpeg -c copy (stream copy, key-frame aligned, no re-encode); useful for coarse cuts.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    _check_ffmpeg()
    start_sec = parse_timecode(args.start)
    end_sec = parse_timecode(args.end)
    cut_clip(args.input, start_sec, end_sec, args.output, stream_copy=args.copy)
    mode = "stream-copy" if args.copy else "re-encode"
    print(
        f"[ok] cut {args.start} -> {args.end} ({end_sec - start_sec:.2f}s, {mode}) -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
