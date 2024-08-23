import argparse
import os
from datetime import datetime

import fontforge

import src.params as PARAMS
import src.properties as PROPERTY
from src.font_patcher import _patch
from src.utils import (
    clear_font_glyph,
    fix_all_glyph_points,
    make_italic,
    resize_all_glyph_width,
    resize_all_scale,
    resize_glyph_width,
    set_font_em,
)

PROPERTY.FAMILYNAME = "RobotoMonoJP-Mono"


def arg_parse():
    parser = argparse.ArgumentParser(description="Generate Font")
    parser.add_argument(
        "--jp_font",
        type=str,
        default="./src/fonts/IBMPlexSansJP/IBMPlexSansJP-Regular.ttf",
    )
    parser.add_argument(
        "--en_font", type=str, default="./src/fonts/RobotoMono/RobotoMono-Regular.ttf"
    )
    parser.add_argument("--style", type=str, default="Regular")
    return parser.parse_args()


def new_font(style):
    font = fontforge.font()
    style_property = PROPERTY.STYLE_PROPERTIES[style]

    font.ascent = PROPERTY.ASCENT
    font.descent = PROPERTY.DESCENT
    font.italicangle = PROPERTY.ITALIC_ANGLE if "Italic" in style else 0
    font.upos = PROPERTY.UNDERLINE_POS
    font.uwidth = PROPERTY.UNDERLINE_HEIGHT
    font.familyname = PROPERTY.FAMILYNAME
    font.copyright = PROPERTY.COPYRIGHT
    font.encoding = PROPERTY.ENCODING
    font.fontname = PROPERTY.FAMILYNAME + "-" + style
    font.fullname = PROPERTY.FAMILYNAME + "-" + style
    font.version = PROPERTY.VERSION

    subfamily = "".join([" " + c if c.isupper() else c for c in style]).lstrip()
    font.appendSFNTName("English (US)", "SubFamily", subfamily)
    font.appendSFNTName(
        "English (US)",
        "UniqueID",
        "; ".join(
            [
                f"FontForge {fontforge.version()}",
                PROPERTY.FAMILYNAME + " " + style,
                PROPERTY.VERSION,
                datetime.today().strftime("%F"),
            ]
        ),
    )

    font.gasp_version = 1
    font.gasp = (
        (65535, ("gridfit", "antialias", "symmetric-smoothing", "gridfit+smoothing")),
    )

    font.weight = style_property.weight
    font.os2_weight = style_property.os2_weight
    font.os2_width = 5  # Medium (100%)
    font.os2_stylemap = style_property.os2_stylemap
    font.os2_vendor = "mjun"  # me
    font.os2_panose = (  # https://monotype.github.io/panose/pan1.htm
        2,  # Family Kind = 2-Latin: Text and Display
        11,  # Serif Style = Nomal Sans
        style_property.panose_weight,  # Weight
        9,  # Proportion = 9-Monospaced
        3,  # Contrast = 3-Very Low
        2,  # Stroke Variation = 2-No Variation
        2,  # Arm Style = 2-Straight Arms/Horizontal
        style_property.panose_letterform,  # Letterform
        2,  # Midline = 2-Standard/Trimmed
        4,  # X-height = 4-Constant/Large
    )

    # typoascent, typodescent is generic version for above.
    # the `_add` version is for setting offsets.
    font.os2_typoascent = PROPERTY.ASCENT
    font.os2_typodescent = -PROPERTY.DESCENT
    font.os2_typoascent_add = 0
    font.os2_typodescent_add = 0

    # winascentwindescent is typoascent/typodescent for Windows.
    font.os2_winascent = PROPERTY.ASCENT
    font.os2_windescent = PROPERTY.DESCENT
    font.os2_winascent_add = 0
    font.os2_windescent_add = 0

    # winascentwindescent is typoascent/typodescent for macOS.
    font.hhea_ascent = PROPERTY.ASCENT
    font.hhea_descent = -PROPERTY.DESCENT
    font.hhea_ascent_add = 0
    font.hhea_descent_add = 0

    # linegap is for gap between lines.  The `hhea_` version is for macOS.
    font.os2_typolinegap = 0
    font.hhea_linegap = 0

    return font


def get_jp_font(path: str) -> fontforge.font:
    font = fontforge.open(path)
    font.encoding = PROPERTY.ENCODING

    # カーニング情報を削除する。
    for lookup in font.gpos_lookups:
        if (
            lookup.startswith("'halt'")
            or lookup.startswith("'vhal'")
            or lookup.startswith("'kern'")
            or lookup.startswith("'vkrn'")
            or lookup.startswith("'palt'")
            or lookup.startswith("'vpal'")
        ):
            font.removeLookup(lookup)

    for lookup in font.gsub_lookups:
        if (
            lookup.startswith("'vert'")  # 縦書き用のlookup
            or lookup.startswith("'vrt2'")  # 縦書き用のlookup
            or lookup.startswith("'liga'")  # リガチャ(合字)用のlookup
        ):
            for subtable in font.getLookupSubtables(lookup):
                font.removeLookupSubtable(subtable)
            font.removeLookup(lookup)

    # 縦書きグリフは使わないので削除する。
    for glyph in font.glyphs():
        if glyph.unicode != -1:
            continue
        name = glyph.glyphname
        if name.endswith(".rotat"):
            clear_font_glyph(font, name)

    clear_font_glyph(font, *PARAMS.LIGATURE)  # リガチャ(合字)を削除
    clear_font_glyph(font, *PARAMS.ASCII_SYMBOLS)
    clear_font_glyph(font, *PARAMS.ASCII_NUMBERS)
    clear_font_glyph(font, *PARAMS.ASCII_SYMBOLS_2)
    clear_font_glyph(font, *PARAMS.ALPHABET)
    clear_font_glyph(font, *PARAMS.OTHER_GLYPHS)
    clear_font_glyph(font, 0x20AC)  # €
    clear_font_glyph(font, 0x2190, 0x21F5)  # arrow
    clear_font_glyph(font, 0x2200, 0x22A5)  # math symbol
    clear_font_glyph(font, 0x2116)  # №
    clear_font_glyph(font, 0x2122)  # ™
    clear_font_glyph(font, 0x23A7, 0x23AD)  # curly bracket
    clear_font_glyph(font, 0x2500, 0x2595)  # border symbol
    clear_font_glyph(font, 0x25A0, 0x25EF)  # block symbol

    set_font_em(font, PROPERTY.ASCENT, PROPERTY.DESCENT, PROPERTY.EM)

    # Shrink to 1:2
    resize_glyph_width(font[0x2103], PROPERTY.EM // 2)  # ℃
    resize_glyph_width(font[0x2109], PROPERTY.EM // 2)  # ℉
    resize_glyph_width(font[0x2121], PROPERTY.EM // 2)  # ℡
    resize_glyph_width(font[0x212B], PROPERTY.EM // 2)  # Å

    # Fix width (Note that I don't know the meaning of the following glyphs)
    # unkown scale: 1257 name: section
    # unkown scale: 1187 name: dagger.prop
    # unkown scale: 1187 name: daggerdbl.prop
    # unkown scale: 1396 name: paragraph
    # unkown scale: 2799 name: perthousand.full
    # unkown scale: 1003 name: degree
    # unkown scale: 1290 name: plusminus
    # unkown scale: 1290 name: multiply
    # unkown scale: 1290 name: divide
    # unkown scale: 1290 name: zero.zero
    # unkown scale: 2052 name: uni51F0
    # unkown scale: 1245 name: a.alt01
    # unkown scale: 1245 name: g.alt01
    # unkown scale: 1142 name: g.alt02
    # unkown scale: 1290 name: zero.alt01
    for name in (
        "section",
        "dagger.prop",
        "daggerdbl.prop",
        "paragraph",
        "degree",
        "plusminus",
        "multiply",
        "divide",
        "zero.zero",
        "uni51F0",
        "a.alt01",
        "g.alt01",
        "g.alt02",
        "zero.alt01",
    ):
        resize_glyph_width(font[name], PROPERTY.EM // 2)
    for name in ("perthousand.full", "uni51F0"):
        resize_glyph_width(font[name], PROPERTY.EM)

    resize_all_scale(font, 0.9)
    fix_all_glyph_points(font, round=True)

    font.selection.all()
    font.unlinkReferences()
    font.selection.none()

    return font


def get_en_font(path: str) -> fontforge.font:
    font = fontforge.open(path)
    font.encoding = PROPERTY.ENCODING
    set_font_em(font, PROPERTY.ASCENT, PROPERTY.DESCENT, PROPERTY.EM)
    resize_all_glyph_width(font, PROPERTY.EM // 2)
    fix_all_glyph_points(font, round=True)
    return font


def main():
    args = arg_parse()
    os.makedirs("tmp", exist_ok=True)

    base_font = new_font(args.style)

    # モノスペースフォントをマージする
    print("en_font merging")
    en_font = get_en_font(args.en_font)
    en_font.generate("./tmp/en_tmp.ttf")
    en_font.close()
    en_font = fontforge.open("./tmp/en_tmp.ttf")
    en_font.encoding = PROPERTY.ENCODING
    base_font.mergeFonts(en_font)
    en_font.close()
    print("en_font merged")

    # 日本語フォントをマージする
    print("jp_font merging")
    jp_font = get_jp_font(args.jp_font)
    jp_font.generate("./tmp/jp_tmp.ttf")
    jp_font.close()
    jp_font = fontforge.open("./tmp/jp_tmp.ttf")
    base_font.mergeFonts(jp_font)
    for glyph in jp_font.glyphs():
        if not glyph.isWorthOutputting:
            # 削除すべきglyphは消す
            base_font.selection.select(glyph)
            base_font.clear()
            base_font.selection.none()
            continue
        code = glyph.unicode
        if code == -1:
            continue
        if glyph.altuni is not None:
            base_font[code].altuni = glyph.altuni
        base_font[code].unicode = code
    jp_font.close()
    print("jp_font merged")

    base_font.selection.all()
    base_font.removeOverlap()
    base_font.round()
    base_font.autoHint()
    base_font.autoInstr()
    base_font.selection.none()

    if "Italic" in args.style:
        make_italic(base_font, PROPERTY.ITALIC_ANGLE)
        fix_all_glyph_points(base_font, round=True, addExtrema=True)
    else:
        fix_all_glyph_points(base_font, addExtrema=True)

    _patch(base_font)
    os.makedirs(PROPERTY.FAMILYNAME, exist_ok=True)
    base_font.generate(f"{PROPERTY.FAMILYNAME}/{PROPERTY.FAMILYNAME}-{args.style}.ttf")
    base_font.close()
    print(
        "font generated: ",
        f"{PROPERTY.FAMILYNAME}/{PROPERTY.FAMILYNAME}-{args.style}.ttf",
    )


if __name__ == "__main__":
    main()
