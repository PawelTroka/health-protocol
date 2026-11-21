"""Readable HTML foregrounds without changing health scores or classifications.

WCAG 2.2 SC 1.4.3 requires at least 4.5:1 for ordinary text. Use the actual
report backgrounds and unrounded sRGB contrast; retain the original hue by
scaling its channels only when its foreground is too light.
https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
"""

from functools import lru_cache
import re


PAGE_BACKGROUND = "#ffffff"
ALTERNATE_ROW_BACKGROUND = "#fafbfd"
TEXT_BACKGROUNDS = (PAGE_BACKGROUND, ALTERNATE_ROW_BACKGROUND)
MIN_TEXT_CONTRAST = 4.5


def _rgb(color):
    if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError("Report colors must be six-digit hexadecimal colors.")
    return tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))


def _luminance(color):
    channels = [value / 255 for value in _rgb(color)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
              for value in channels]
    return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast_ratio(foreground, background):
    """WCAG relative-luminance ratio, without rounding near the threshold."""
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


@lru_cache(maxsize=1024)
def readable_text_color(color):
    """Keep a readable color; otherwise darken it for both light report surfaces."""
    channels = _rgb(color)

    def scaled(level):
        return "#" + "".join(f"{value * level // 255:02x}" for value in channels)

    def readable(candidate):
        return all(contrast_ratio(candidate, background) >= MIN_TEXT_CONTRAST
                   for background in TEXT_BACKGROUNDS)

    original = scaled(255)
    if readable(original):
        return original
    # Black is readable on both fixed light surfaces. Find the brightest
    # passing scale on the 8-bit channel grid, always returning a passing color.
    low, high = 0, 255
    while high - low > 1:
        middle = (low + high) // 2
        if readable(scaled(middle)):
            low = middle
        else:
            high = middle
    return scaled(low)
