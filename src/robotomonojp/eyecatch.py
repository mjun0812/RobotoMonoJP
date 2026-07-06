"""terminal風アイキャッチSVGの生成.

指定フォントのglyph outlineをSVG pathに変換して埋め込むため、
閲覧環境にフォントが無くても指定フォントの字形で表示される。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

# 配色 (docs/images/font_preview.png とdotfiles bannerを踏襲)
BACKDROP_COLOR = "#4A90E2"
WINDOW_COLOR = "#282C34"
WINDOW_BORDER_COLOR = "#3E4451"
ACCENT_COLOR = "#E06C75"
TEXT_COLOR = "#ABB2BF"
LIGHT_COLORS = ("#FF5F57", "#FEBC2E", "#28C840")
TITLE_GRADIENT = ("#7AA2F7", "#BB9AF7", "#7DCFFF")

CANVAS_WIDTH = 1360
CANVAS_HEIGHT = 670
WINDOW_X = 112
WINDOW_Y = 88
WINDOW_WIDTH = CANVAS_WIDTH - WINDOW_X * 2
WINDOW_HEIGHT = CANVAS_HEIGHT - WINDOW_Y * 2
CONTENT_X = 148

TITLE_SIZE = 54
BODY_SIZE = 32
LINE_HEIGHT = 46

# Nerd Fonts行に載せるアイコン (Powerline, Devicons, Codicons, Font Awesome, Font Logos, IEC Power)
NERD_ICON_CODES = (0xE0A0, 0xE0B0, 0xE702, 0xE718, 0xEA60, 0xF015, 0xF121, 0xF179, 0xF31B, 0x23FB)

# (テキスト, 色種別) の行。色種別: title / accent / text
SAMPLE_LINES: list[tuple[str, str]] = [
    ("# Alphabet", "accent"),
    ("abcdefghijklmnopqrstuvwxyz", "text"),
    ("ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789", "text"),
    ("# Japanese", "accent"),
    ("あいうえお アイウエオ 漢字日本語 ｱｲｳｴｵ", "text"),
    ("# Nerd Fonts", "accent"),
    ("  ".join(chr(c) for c in NERD_ICON_CODES), "text"),
]


class _FontOutline:
    """fontToolsでglyph outlineをSVG path化するヘルパー."""

    def __init__(self, font_path: Path) -> None:
        """フォントを読み込み、glyph set / cmap / upem を用意する."""
        from fontTools.ttLib import TTFont

        self._font = TTFont(str(font_path))
        self._glyph_set = self._font.getGlyphSet()
        self._cmap: dict[int, str] = self._font.getBestCmap() or {}
        self.upem: int = cast(Any, self._font["head"]).unitsPerEm

    def family_name(self) -> str:
        """フォントのfamily名を返す."""
        name = self._font["name"].getBestFamilyName()
        return name or "Unknown"

    def text_paths(self, text: str) -> str:
        """テキストをglyphごとの <path> 群 (fontユニット座標) に変換する."""
        from fontTools.pens.svgPathPen import SVGPathPen

        parts: list[str] = []
        x = 0
        for ch in text:
            glyph_name = self._cmap.get(ord(ch))
            if glyph_name is None:
                x += self.upem // 2
                continue
            glyph = self._glyph_set[glyph_name]
            pen = SVGPathPen(self._glyph_set)
            glyph.draw(pen)
            commands = pen.getCommands()
            if commands:
                parts.append(f'<path transform="translate({x} 0)" d="{commands}"/>')
            x += glyph.width
        return "".join(parts)


def _text_group(outline: _FontOutline, text: str, x: int, y: int, size: float, fill: str) -> str:
    """テキスト1行をSVGグループにする. yはbaseline位置 (px)."""
    scale = size / outline.upem
    paths = outline.text_paths(text)
    return f'<g transform="translate({x} {y}) scale({scale:.6f} -{scale:.6f})" fill="{fill}">{paths}</g>'


def generate_eyecatch(font_path: Path, output: Path, title: str | None = None) -> Path:
    """指定フォントでterminal風アイキャッチSVGを生成する.

    Args:
        font_path: 描画に使うttf/otfのpath.
        output: 出力先SVGのpath.
        title: タイトル文字列. 未指定ならフォントのfamily名.
    """
    outline = _FontOutline(font_path)
    title_text = title or outline.family_name()

    body: list[str] = []
    lights = "".join(
        f'<circle cx="{CONTENT_X + 4 + i * 39}" cy="{WINDOW_Y + 44}" r="11" fill="{color}"/>'
        for i, color in enumerate(LIGHT_COLORS)
    )
    body.append(lights)

    baseline = WINDOW_Y + 132
    body.append(_text_group(outline, title_text, CONTENT_X, baseline, TITLE_SIZE, "url(#title)"))
    baseline += 24

    for text, kind in SAMPLE_LINES:
        baseline += LINE_HEIGHT
        fill = ACCENT_COLOR if kind == "accent" else TEXT_COLOR
        body.append(_text_group(outline, text, CONTENT_X, baseline, BODY_SIZE, fill))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" role="img" aria-label="{title_text}">
  <defs>
    <linearGradient id="title" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{TITLE_GRADIENT[0]}"/>
      <stop offset="50%" stop-color="{TITLE_GRADIENT[1]}"/>
      <stop offset="100%" stop-color="{TITLE_GRADIENT[2]}"/>
    </linearGradient>
  </defs>
  <rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="{BACKDROP_COLOR}"/>
  <rect x="{WINDOW_X}" y="{WINDOW_Y}" width="{WINDOW_WIDTH}" height="{WINDOW_HEIGHT}" rx="16" fill="{WINDOW_COLOR}" stroke="{WINDOW_BORDER_COLOR}"/>
  {"".join(body)}
</svg>
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    return output
