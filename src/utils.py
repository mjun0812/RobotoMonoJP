import math
from typing import Optional

import fontforge
import psMat


def clear_font_glyph(
    font: fontforge.font,
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> None:
    if end is None:
        font.selection.select(start)
    else:
        font.selection.select(("ranges",), start, end)
    font.clear()
    font.selection.none()


def print_pdf(font, path):
    fontforge.printSetup("pdf-file")
    font.printSample("fontdisplay", 18, "", path)


def resize_glyph_width(glyph, new_width: int) -> None:
    old_width = glyph.width
    mat = psMat.scale(float(new_width) / old_width, 1)
    glyph.transform(mat)
    glyph.width = new_width


def resize_all_glyph_width(font, new_width: int) -> None:
    for glyph in font.glyphs():
        if glyph.width == new_width:
            continue
        if glyph.width != 0:
            fix_scale_mat = psMat.scale(float(new_width) / glyph.width)
            glyph.transform(fix_scale_mat)
        glyph.width = new_width


def resize_all_scale(
    font: fontforge.font,
    scale: float,
    translate_x: Optional[float] = None,
    translate_y: Optional[float] = None,
) -> None:
    em = font.em
    x_to_center = em * (1 - scale) / 2

    scale_mat = [psMat.scale(scale) for _ in range(2)]
    trans_mat = [psMat.translate(x) for x in (x_to_center, x_to_center / 2)]
    mat = [psMat.compose(scale_mat[i], trans_mat[i]) for i in range(2)]

    for glyph in font.glyphs():
        width = glyph.width
        if width == em:
            glyph.transform(mat[0])
            glyph.width = em
        elif width == em // 2:
            glyph.transform(mat[1])
            glyph.width = em // 2

        if translate_x is not None:
            glyph.transform(psMat.translate(translate_x, 0))
        if translate_y is not None:
            glyph.transform(psMat.translate(0, translate_y))


def set_font_em(font, ascent: int, descent: int, em: int) -> None:
    old_em = font.em
    font.selection.all()
    font.unlinkReferences()
    font.ascent = round(float(ascent) / em * old_em)
    font.descent = round(float(descent) / em * old_em)
    font.em = em
    font.selection.none()


def fix_all_glyph_points(font, round: bool = False, addExtrema: bool = False) -> None:
    for glyph in font.glyphs():
        if round:
            glyph.round()
        if addExtrema:
            glyph.addExtrema("all")


def make_italic(font, italic_angle) -> None:
    rot_rad = -1 * italic_angle * math.pi / 180
    transform_mat = psMat.skew(rot_rad)

    def selectMore(start, end=None):
        nonlocal font
        if end is None:
            font.selection.select(("more", "encoding"), start)
        else:
            font.selection.select(("more", "ranges", "encoding"), start, end)

    selectMore(0x21, 0x217F)
    selectMore(0x2460, 0x24EA)
    selectMore(0x2768, 0x277E)
    selectMore(0x27E6, 0x27EB)
    selectMore(0x2987, 0x2998)
    selectMore(0x2E18)
    selectMore(0x2E22, 0x2E2E)
    selectMore(0x2E8E, 0xFFE5)
    selectMore(0x1F100)
    selectMore(0x20B9F, 0x2F920)
    # NOTE: After 0x110000, codepoint is defferent in Reguler and Bold.
    selectMore(".notdef", "uni301F.half")
    selectMore("acute.half", "zero.alt01")
    font.transform(transform_mat)
    font.selection.none()
