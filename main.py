import os
from datetime import datetime

import fontforge
import psMat

import src.params as PARAMS
import src.properties as PROPERTY
from src.font_patcher import _patch
from src.utils import clear_font_glyph

# ### サイズ関係 ###
WIDTH = 1299

# 余白をもたせる。PROPERTYではグリフギリギリを設定して，こちらでは大きい値を設定する
OS2_ASCENT = 2146
OS2_DESCENT = 555


def new_font(style="Regular"):
    font = fontforge.font()
    prop = PROPERTY.STYLE_PROPERTIES[style]

    # ### Font Height ###
    font.ascent = PROPERTY.ASCENT
    font.descent = PROPERTY.DESCENT
    font.em = PROPERTY.EM
    font.italicangle = PROPERTY.ITALIC_ANGLE if "Italic" in style else 0
    font.upos = PROPERTY.UNDERLINE_POS
    font.uwidth = PROPERTY.UNDERLINE_HEIGHT

    # ### Font Info ###
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

    font.weight = prop.weight
    font.os2_weight = prop.os2_weight
    font.os2_width = 5  # Medium (w/h = 1.000)
    font.os2_fstype = 4  # Printable Document (suitable for SF Mono)
    font.os2_family_class = 2057  # SS Typewriter Gothic

    # refer: [The 'OS/2' table]
    # (https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6OS2.html)
    font.os2_panose = (
        2,  # Latin: Text and Display
        11,  # Nomal Sans
        prop.panose_weight,
        9,  # Monospaced
        2,  # None
        2,  # No Variation
        3,  # Straight Arms/Wedge
        prop.panose_letterform,
        2,  # Standard/Trimmed
        7,  # Ducking/Large
    )

    # winascent & windescent is for setting the line height for Windows.
    font.os2_winascent = OS2_ASCENT
    font.os2_windescent = OS2_DESCENT
    font.os2_winascent_add = 0
    font.os2_windescent_add = 0

    # hhea_ascent, hhea_descent is the macOS version for winascent & windescent.
    font.hhea_ascent = OS2_ASCENT
    font.hhea_descent = -OS2_DESCENT
    font.hhea_ascent_add = 0
    font.hhea_descent_add = 0
    # linegap is for gap between lines.
    font.hhea_linegap = 0

    # typoascent, typodescent is generic version for above.
    font.os2_typoascent = OS2_ASCENT
    font.os2_typodescent = -OS2_DESCENT
    font.os2_typoascent_add = 0
    font.os2_typodescent_add = 0
    font.os2_typolinegap = 0

    return font


def modify_plex(font_path):
    font = fontforge.open(font_path)
    OLD_JP_ASCENT = font.ascent
    SCALE = PROPERTY.ASCENT / OLD_JP_ASCENT + 0.10

    font.encoding = PROPERTY.ENCODING

    # 縦の長さをスケール変換
    font.selection.all()
    font.unlinkReferences()
    font.ascent = PROPERTY.ASCENT
    font.descent = PROPERTY.DESCENT
    font.em = PROPERTY.EM
    # 文字を全体的にスケール変換(SCALEを要調整)
    font.selection.all()
    for glyph in font.glyphs():
        # 削除すべきglyphは消す
        if not glyph.isWorthOutputting:
            font.selection.select(glyph)
            font.clear()
            continue

        glyph.transform(psMat.scale(SCALE, SCALE))

        if glyph.encoding in PARAMS.HANKAKU_KANA:
            # 半角カナは半角へ
            glyph.width = WIDTH
        elif glyph.encoding in PARAMS.FULLWIDTH_CODES_LIST:
            # 全角文字は全角へ
            glyph.width = WIDTH + 550

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

    font.generate("./tmp/jp_tmp.ttf")
    font.close()


def main():
    os.makedirs("tmp", exist_ok=True)

    font = new_font()
    font.mergeFonts("./src/fonts/RobotoMono/RobotoMono-Regular.ttf")

    modify_plex("./src/fonts/IBMPlexSansJP/IBMPlexSansJP-Regular.ttf")
    jp_font = fontforge.open("./tmp/jp_tmp.ttf")
    font.mergeFonts("./tmp/jp_tmp.ttf")
    for glyph in jp_font.glyphs():
        code = glyph.unicode
        if code == -1:
            continue
        try:
            if glyph.altuni is not None:
                font[code].altuni = glyph.altuni
            font[code].unicode = code
        except TypeError:
            pass
    jp_font.close()

    font.selection.all()
    font.removeOverlap()
    font.round()
    font.autoHint()
    font.autoInstr()
    font.selection.none()

    _patch(font)
    font.generate("./RobotoMonoJP/RobotoMonoJP-Regular.ttf")
    font.close()


if __name__ == "__main__":
    main()
