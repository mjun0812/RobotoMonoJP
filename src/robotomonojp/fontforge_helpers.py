"""FontForge Python API を薄くラップするヘルパー群. 旧 src/utils.py から移植."""

from __future__ import annotations

import math
from typing import Any, cast

# fontforge / psMat はDocker (ubuntu:24.04 の python3-fontforge) に依存する.
# 開発マシンでは import できないため、type checker からは Any として扱う.
try:  # pragma: no cover - import guard
    import fontforge as _fontforge  # type: ignore[import-not-found]
    import psMat as _psmat  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    _fontforge = None
    _psmat = None

fontforge: Any = cast(Any, _fontforge)
psMat: Any = cast(Any, _psmat)


def clear_font_glyph(font: Any, start: int, end: int | None = None) -> None:
    """指定Unicodeレンジをクリアする."""
    if end is None or end == start:
        font.selection.select(start)
    else:
        font.selection.select(("ranges",), start, end)
    font.clear()
    font.selection.none()


def clear_font_glyph_by_name(font: Any, name: str) -> None:
    """glyph名指定でクリア."""
    font.selection.select(name)
    font.clear()
    font.selection.none()


def resize_glyph_width(glyph: Any, new_width: int) -> None:
    """1つのglyphの幅を new_width にリサイズし、そのままscale変換する."""
    old_width = glyph.width
    if old_width == 0:
        glyph.width = new_width
        return
    mat = psMat.scale(float(new_width) / old_width, 1)
    glyph.transform(mat)
    glyph.width = new_width


def resize_all_glyph_width(font: Any, new_width: int) -> None:
    """全glyphの幅を new_width に揃える."""
    for glyph in font.glyphs():
        if glyph.width == new_width:
            continue
        if glyph.width != 0:
            mat = psMat.scale(float(new_width) / glyph.width)
            glyph.transform(mat)
        glyph.width = new_width


def resize_all_scale(
    font: Any,
    scale: float,
    translate_x: float | None = None,
    translate_y: float | None = None,
    full_width: int | None = None,
    half_width: int | None = None,
) -> None:
    """全glyphを scale 倍にし、中央にtranslateしてから追加のtranslateを適用."""
    em = font.em
    x_to_center = em * (1 - scale) / 2
    target_full_width = full_width if full_width is not None else em
    target_half_width = half_width if half_width is not None else em // 2

    scale_mat = [psMat.scale(scale) for _ in range(2)]
    trans_mat = [psMat.translate(x) for x in (x_to_center, x_to_center / 2)]
    mat = [psMat.compose(scale_mat[i], trans_mat[i]) for i in range(2)]

    for glyph in font.glyphs():
        width = glyph.width
        if width == em:
            glyph.transform(mat[0])
            glyph.width = target_full_width
        elif width == em // 2:
            glyph.transform(mat[1])
            glyph.width = target_half_width

        if translate_x is not None:
            glyph.transform(psMat.translate(translate_x, 0))
        if translate_y is not None:
            glyph.transform(psMat.translate(0, translate_y))


def set_font_em(font: Any, ascent: int, descent: int, em: int) -> None:
    """ascent/descent/em を目標値に合わせてフォント全体をスケール."""
    old_em = font.em
    font.selection.all()
    font.unlinkReferences()
    font.ascent = round(float(ascent) / em * old_em)
    font.descent = round(float(descent) / em * old_em)
    font.em = em
    font.selection.none()


def fix_all_glyph_points(font: Any, do_round: bool = False, add_extrema: bool = False) -> None:
    """全glyphに対して round / addExtrema をかける."""
    for glyph in font.glyphs():
        if do_round:
            glyph.round()
        if add_extrema:
            glyph.addExtrema("all")


def skew_matrix(italic_angle: float) -> Any:
    """italic_angle (度) から skew 行列を作る. angleが負なら右上がりのItalic."""
    rot_rad = -1 * italic_angle * math.pi / 180
    return psMat.skew(rot_rad)


def make_italic(font: Any, italic_angle: float) -> None:
    """フォント全体を skew してItalic化する. 旧 utils.make_italic を移植."""
    transform_mat = skew_matrix(italic_angle)

    def select_more(start: int | str, end: int | str | None = None) -> None:
        if end is None:
            font.selection.select(("more", "encoding"), start)
        else:
            font.selection.select(("more", "ranges", "encoding"), start, end)

    select_more(0x21, 0x217F)
    select_more(0x2460, 0x24EA)
    select_more(0x2768, 0x277E)
    select_more(0x27E6, 0x27EB)
    select_more(0x2987, 0x2998)
    select_more(0x2E18)
    select_more(0x2E22, 0x2E2E)
    select_more(0x2E8E, 0xFFE5)
    select_more(0x1F100)
    select_more(0x20B9F, 0x2F920)
    # コードポイントを名前で指定する範囲 (Regular/Boldでcodepointが異なるため).
    try:
        select_more(".notdef", "uni301F.half")
        select_more("acute.half", "zero.alt01")
    except Exception:  # noqa: BLE001 - glyph名が無い環境ではスキップ
        pass
    font.transform(transform_mat)
    font.selection.none()


def remove_lookups(
    font: Any, gsub_prefixes: tuple[str, ...], gpos_prefixes: tuple[str, ...]
) -> None:
    """指定prefixで始まる GSUB / GPOS lookup を削除する."""
    for lookup in list(font.gsub_lookups):
        if lookup.startswith(gsub_prefixes):
            for subtable in font.getLookupSubtables(lookup):
                font.removeLookupSubtable(subtable)
            font.removeLookup(lookup)
    for lookup in list(font.gpos_lookups):
        if lookup.startswith(gpos_prefixes):
            font.removeLookup(lookup)


def remove_glyphs_with_features(font: Any, features: tuple[str, ...]) -> None:
    """指定OpenType featureに紐づくglyphを削除する (リガチャ削除に使用)."""
    to_clear: list[int] = []
    for glyph in font.glyphs():
        pos_sub = glyph.getPosSub("*")
        if any(feature in entry for entry in pos_sub for feature in features):
            to_clear.append(glyph.encoding)
    for enc in to_clear:
        font.selection.select(enc)
        font.clear()
    font.selection.none()


def remove_vertical_variants(font: Any) -> None:
    """名前が .rotat で終わる縦書きvariant glyphを削除."""
    to_clear: list[str] = []
    for glyph in font.glyphs():
        if glyph.unicode != -1:
            continue
        if glyph.glyphname.endswith(".rotat"):
            to_clear.append(glyph.glyphname)
    for name in to_clear:
        clear_font_glyph_by_name(font, name)
