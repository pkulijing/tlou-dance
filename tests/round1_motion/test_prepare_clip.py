"""TDD for round1_motion.prepare_clip — 时间码解析子模块。

只测纯函数 parse_timecode；ffmpeg 切片走子进程，属外部系统集成，按 Constitution 例外不在此 TDD。
"""

import pytest

from round1_motion.prepare_clip import parse_timecode


class TestParseTimecodeValidFormats:
    """合法输入：HH:MM:SS / MM:SS / SS（皆可带 .mmm 毫秒）"""

    def test_full_form_zero(self):
        assert parse_timecode("00:00:00") == 0.0

    def test_full_form_zero_with_ms(self):
        assert parse_timecode("00:00:00.000") == 0.0

    def test_full_form_with_ms(self):
        # 1h 23m 45.678s
        assert parse_timecode("01:23:45.678") == pytest.approx(1 * 3600 + 23 * 60 + 45 + 0.678)

    def test_mm_ss_form(self):
        # 1m 30s
        assert parse_timecode("1:30") == 90.0

    def test_mm_ss_with_ms(self):
        assert parse_timecode("0:01.500") == 1.5

    def test_seconds_only(self):
        assert parse_timecode("30") == 30.0

    def test_seconds_only_with_ms(self):
        assert parse_timecode("23.5") == 23.5

    def test_h_padding_optional(self):
        # 不要求强制 0-pad
        assert parse_timecode("1:0:0") == 3600.0


class TestParseTimecodeInvalidFormats:
    """非法输入：应抛 ValueError"""

    def test_empty_string(self):
        with pytest.raises(ValueError):
            parse_timecode("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError):
            parse_timecode("   ")

    def test_non_numeric(self):
        with pytest.raises(ValueError):
            parse_timecode("abc")

    def test_too_many_colons(self):
        with pytest.raises(ValueError):
            parse_timecode("1:2:3:4")

    def test_empty_segment_leading_colon(self):
        with pytest.raises(ValueError):
            parse_timecode(":12")

    def test_empty_segment_trailing_colon(self):
        with pytest.raises(ValueError):
            parse_timecode("12:")

    def test_minutes_overflow(self):
        with pytest.raises(ValueError):
            parse_timecode("00:60:00")

    def test_seconds_overflow(self):
        with pytest.raises(ValueError):
            parse_timecode("00:00:60")

    def test_negative(self):
        with pytest.raises(ValueError):
            parse_timecode("-1:00:00")


class TestParseTimecodeNonString:
    """非字符串输入：应抛 TypeError"""

    def test_none(self):
        with pytest.raises(TypeError):
            parse_timecode(None)  # type: ignore[arg-type]

    def test_int(self):
        with pytest.raises(TypeError):
            parse_timecode(123)  # type: ignore[arg-type]


class TestParseTimecodeRoundtrip:
    """随机往返一致性：浮点秒 → 格式化 → parse 应回到同值（容忍 ms 精度）"""

    @pytest.mark.parametrize(
        "seconds",
        [
            0.0,
            0.001,
            59.999,
            60.0,
            3599.5,
            3600.0,
            3661.123,
            7325.5,  # 2:02:05.500
        ],
    )
    def test_roundtrip(self, seconds):
        # 简单格式化为 HH:MM:SS.mmm
        h = int(seconds // 3600)
        rest = seconds - h * 3600
        m = int(rest // 60)
        s = rest - m * 60
        formatted = f"{h:02d}:{m:02d}:{s:06.3f}"
        assert parse_timecode(formatted) == pytest.approx(seconds, abs=0.001)
