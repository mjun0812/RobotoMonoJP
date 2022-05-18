import fontforge
from datetime import datetime
import psMat
import os

from font_patcher import patch

# 半角カナ等の日本語半角系
HANKAKU_KANA = list(range(0xFF61, 0xFF9F))
# 全角文字
FULLWIDTH_HIRAGANA_KATAKANA = list(range(0x3040, 0x30FF))
FULLWIDTH_CJK_UNIFIED = list(range(0x4E00, 0x9FCF))
FULLWIDTH_CJK_COMPATI = list(range(0xF900, 0xFAFF))
FULLWIDTH_CJK_UNIFIED_EX_A = list(range(0x3400, 0x4DBF))
FULLWIDTH_CJK_UNIFIED_EX_B = list(range(0x20000, 0x2A6DF))
FULLWIDTH_CJK_UNIFIED_EX_C = list(range(0x2A700, 0x2B73F))
FULLWIDTH_CJK_UNIFIED_EX_D = list(range(0x2B740, 0x2B81F))
FULLWIDTH_CJK_COMPATI_SUPP = list(range(0x2F800, 0x2FA1F))
FULLWIDTH_CODES = (
    FULLWIDTH_HIRAGANA_KATAKANA
    + FULLWIDTH_CJK_UNIFIED
    + FULLWIDTH_CJK_COMPATI
    + FULLWIDTH_CJK_UNIFIED_EX_A
    + FULLWIDTH_CJK_UNIFIED_EX_B
    + FULLWIDTH_CJK_UNIFIED_EX_C
    + FULLWIDTH_CJK_UNIFIED_EX_D
    + FULLWIDTH_CJK_COMPATI_SUPP
)

FAMILY = "RobotoMono"
FAMILY_SUFFIX = "JP Nerd"
FULLNAME = f"{FAMILY} {FAMILY_SUFFIX}"
FILENAME = FULLNAME.replace(" ", "")
VERSION = "3.0"

# ### 斜体 ###
ITALIC = "Italic"
ITALIC_ANGLE = -10

# ### サイズ関係 ###
ASCENT = 1638
DESCENT = 410
EM = ASCENT + DESCENT
UNDERLINE_POS = -200
UNDERLINE_HEIGHT = 100
WIDTH = 1299

# 余白をもたせる
# 上の値はグリフギリギリを設定して，こちらでは大きい値を設定する
OS2_ASCENT = 2146
OS2_DESCENT = 555


ENCODING = "UnicodeFull"
ME = "Junya Morioka"
MAIL = "mjun@mjunya.com"
YEAR = datetime.now().year
STYLE_PROPERTY = {
    "Regular": {
        "weight": "Book",
        "os2_weight": 400,
        "panose_weight": 5,
        "panose_letterform": 2,
    },
    "Bold": {
        "weight": "Bold",
        "os2_weight": 700,
        "panose_weight": 8,
        "panose_letterform": 2,
    },
    "RegularItalic": {
        "weight": "Book",
        "os2_weight": 400,
        "panose_weight": 5,
        "panose_letterform": 9,
    },
    "BoldItalic": {
        "weight": "Bold",
        "os2_weight": 700,
        "panose_weight": 8,
        "panose_letterform": 9,
    },
}


def get_base_font():
    prop = STYLE_PROPERTY["Regular"]

    font = fontforge.font()

    # ### Font Height ###
    font.ascent = ASCENT
    font.descent = DESCENT
    font.em = EM

    # ### Italic ###
    font.italicangle = ITALIC_ANGLE

    # ### Underline ###
    font.upos = UNDERLINE_POS
    font.uwidth = UNDERLINE_HEIGHT

    # ### Font Info ###
    font.familyname = FULLNAME
    font.copyright = f"Copyright {YEAR} {ME} {MAIL} All Rights Reserved."
    font.encoding = ENCODING
    font.fontname = FILENAME + "-Regular"
    font.fullname = FILENAME + " Regular"
    font.version = VERSION
    font.appendSFNTName("English (US)", "SubFamily", "Regular")
    font.appendSFNTName(
        "English (US)",
        "UniqueID",
        "; ".join(
            [
                f"FontForge {fontforge.version()}",
                font.fullname,
                font.version,
                datetime.today().strftime("%F"),
            ]
        ),
    )
    font.os2_vendor = "mjun"  # me

    font.weight = prop["weight"]
    font.os2_weight = prop["os2_weight"]
    font.os2_width = 5  # Medium (w/h = 1.000)
    font.os2_fstype = 4  # Printable Document (suitable for SF Mono)
    font.os2_family_class = 2057  # SS Typewriter Gothic

    # refer: [The 'OS/2' table]
    # (https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6OS2.html)
    font.os2_panose = (
        2,  # Latin: Text and Display
        11,  # Nomal Sans
        prop["panose_weight"],
        9,  # Monospaced
        2,  # None
        2,  # No Variation
        3,  # Straight Arms/Wedge
        prop["panose_letterform"],
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
    OLD_JP_ASCENT = 880
    SCALE = ASCENT / OLD_JP_ASCENT + 0.10
    print(f"JP Font convert scale: {SCALE}")

    WIDTH_TLANSLATION = -50
    HEIGHT_TLANSLATION = 0

    font = fontforge.open(font_path)

    # 縦の長さをスケール変換
    font.selection.all()
    font.unlinkReferences()
    font.ascent = ASCENT
    font.descent = DESCENT
    font.em = EM
    # 文字を全体的にスケール変換(SCALEを要調整)
    font.selection.all()
    for glyph in font.glyphs():
        # 削除すべきglyphは消す
        if not glyph.isWorthOutputting:
            font.selection.select(glyph)
            font.clear()
            break

        glyph.transform(psMat.scale(SCALE, SCALE))
        glyph.transform(psMat.translate(WIDTH_TLANSLATION, HEIGHT_TLANSLATION))

        if glyph.encoding in HANKAKU_KANA:
            # 半角カナは半角へ
            glyph.width = WIDTH
        elif glyph.encoding in FULLWIDTH_CODES:
            # 全角文字は全角へ
            glyph.width = WIDTH + 550

    font.generate("./tmp/jp_tmp.ttf")
    font.close()


def print_pdf(font, path):
    fontforge.printSetup("pdf-file")
    font.printSample("fontdisplay", 18, "", path)


def main():
    font = get_base_font()

    font.mergeFonts("./MonoFont/RobotoMono-Regular.ttf")

    os.makedirs("tmp", exist_ok=True)
    modify_plex("./JPFont/IBMPlexSansJP-Regular.ttf")
    font.mergeFonts("./tmp/jp_tmp.ttf")

    # 座標値の補正
    font.selection.all()
    font.removeOverlap()
    font.round()
    font.autoHint()
    font.autoInstr()
    font.selection.none()

    font.generate("./tmp/RobotoMonoJP-Regular.ttf")

    font = patch(font)
    out_path = "./RobotoMonoJP/RobotoMonoJP-Regular"
    font.generate(out_path + ".otf", flags=("opentype"))
    font.generate(out_path + ".ttf")
    print_pdf(font, "./tmp/output.pdf")

    font.close()


if __name__ == "__main__":
    main()
