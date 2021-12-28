import fontforge
from datetime import datetime
import psMat
import os

from font_patcher import patch

FAMILY = "RobotoMono"
FAMILY_SUFFIX = "JP Nerd"
FULLNAME = f"{FAMILY} {FAMILY_SUFFIX}"
FILENAME = FULLNAME.replace(" ", "")
ITALIC = "Italic"
ITALIC_ANGLE = -10
ASCENT = 1638
DESCENT = 410
ENCODING = "UnicodeFull"
UNDERLINE_POS = -200
UNDERLINE_HEIGHT = 100
WIDTH = ASCENT + DESCENT
ME = "Junya Morioka"
MAIL = "mjun@mjunya.com"
YEAR = 2021
EM = ASCENT + DESCENT
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
    font.ascent = ASCENT
    font.descent = DESCENT
    font.italicangle = ITALIC_ANGLE
    font.upos = UNDERLINE_POS
    font.uwidth = UNDERLINE_HEIGHT
    font.familyname = FULLNAME
    font.copyright = f"Copyright {YEAR} {ME} {MAIL} All Rights Reserved."
    font.encoding = ENCODING
    font.fontname = FILENAME + "-Regular"
    font.fullname = FILENAME + " Regular"
    font.version = "1.0"
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
    font.weight = prop["weight"]
    font.os2_weight = prop["os2_weight"]
    font.os2_width = 5  # Medium (w/h = 1.000)
    font.os2_fstype = 4  # Printable Document (suitable for SF Mono)
    font.os2_vendor = "mjun"  # me
    font.os2_family_class = 2057  # SS Typewriter Gothic
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
    # font.os2_winascent = 2146
    font.os2_winascent = 1946
    # font.os2_windescent = 555
    font.os2_windescent = 512
    # the `_add` version is for setting offsets.
    font.os2_winascent_add = 0
    font.os2_windescent_add = 0
    # hhea_ascent, hhea_descent is the macOS version for winascent &
    # windescent.
    # font.hhea_ascent = 2146
    font.hhea_ascent = 1946
    # font.hhea_descent = -555
    font.hhea_descent = -512
    font.hhea_ascent_add = 0
    font.hhea_descent_add = 0
    # typoascent, typodescent is generic version for above.
    # font.os2_typoascent = 2146
    font.os2_typoascent = 1946
    # font.os2_typodescent = -555
    font.os2_typodescent = -500
    font.os2_typoascent_add = 0
    font.os2_typodescent_add = 0
    # linegap is for gap between lines.  The `hhea_` version is for macOS.
    font.os2_typolinegap = 0
    font.hhea_linegap = 0

    return font


def modify_plex(font_path):
    old_em = 1000
    font = fontforge.open(font_path)
    font.selection.all()
    font.unlinkReferences()
    font.ascent = int(float(ASCENT) / EM * old_em)
    font.descent = int(float(DESCENT) / EM * old_em)
    font.em = EM

    scale_size = 1.0
    scale = psMat.scale(scale_size)
    font.selection.all()
    hankaku_kana = (0xFF60, 0xFF9F)
    for glyph in list(font.selection.byGlyphs):
        is_hankaku_kana = glyph.encoding in range(*hankaku_kana)
        x_to_center = EM * (1 - scale_size) / 2 / 2 if is_hankaku_kana else EM * (1 - scale_size) / 2
        trans = psMat.translate(x_to_center, 0)
        mat = psMat.compose(scale, trans)
        glyph.transform(mat)
        glyph.width = EM / 2 if is_hankaku_kana else EM
    font.generate("./tmp/tmp.otf", flags=("opentype",))


def main():
    font = get_base_font()

    font.mergeFonts("./MonoFont/RobotoMono-Regular.ttf")

    os.makedirs("tmp", exist_ok=True)
    modify_plex("./JPFont/IBMPlexSansJP-Regular.otf")
    font.mergeFonts("./tmp/tmp.otf")

    font.autoHint()
    font.autoInstr()
    font.selection.all()

    font.generate("./RobotoMonoJP/RobotoMonoJP-Regular.otf", flags=("opentype"))

    patch("./RobotoMonoJP/RobotoMonoJP-Regular.otf", "")


if __name__ == "__main__":
    main()
