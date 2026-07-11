"""フォント合成のコアロジック. 旧 main_mono.py / main.py 相当."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from . import params, properties
from .config import Config, parse_codepoint_range
from .fontforge_helpers import (
    clear_font_glyph,
    fix_all_glyph_points,
    fontforge,
    make_italic,
    psMat,
    remove_glyphs_with_features,
)
from .patcher import DEFAULT_NERD_FONTS_ROOT
from .patcher import patch as run_nerd_font_patch


@dataclass(frozen=True)
class BuildRequest:
    """generate1回分の入力."""

    config: Config
    style: str  # "Regular" | "Bold" | "Italic" | "BoldItalic"
    version: str
    output_dir: Path
    apply_nerd_font: bool = True
    nerd_fonts_root: Path = DEFAULT_NERD_FONTS_ROOT


def _new_font(
    familyname: str,
    style: str,
    italic_angle: float,
    version: str,
    copyright_text: str,
    vendor: str,
    ascent: int,
    descent: int,
    em: int,
    underline_pos: int,
    underline_height: int,
    os2_ascent: int,
    os2_descent: int,
) -> Any:
    """空フォントを作り、メタデータとOS/2/hheaを埋める."""
    font = fontforge.font()
    style_property = properties.STYLE_PROPERTIES[style]

    font.ascent = ascent
    font.descent = descent
    font.em = em
    font.italicangle = italic_angle if properties.is_italic(style) else 0
    font.upos = underline_pos
    font.uwidth = underline_height
    font.familyname = familyname
    font.copyright = copyright_text
    font.encoding = properties.ENCODING
    font.fontname = f"{familyname}-{style}"
    font.fullname = f"{familyname}-{style}"
    font.version = version

    subfamily = "".join([" " + c if c.isupper() else c for c in style]).lstrip()
    font.appendSFNTName("English (US)", "SubFamily", subfamily)
    font.appendSFNTName(
        "English (US)",
        "UniqueID",
        "; ".join(
            [
                f"FontForge {fontforge.version()}",
                f"{familyname} {style}",
                version,
                date.today().strftime("%F"),
            ]
        ),
    )

    font.gasp_version = 1
    font.gasp = ((65535, ("gridfit", "antialias", "symmetric-smoothing", "gridfit+smoothing")),)

    font.weight = style_property.weight
    font.os2_weight = style_property.os2_weight
    font.os2_width = 5  # Medium (100%)
    font.os2_stylemap = style_property.os2_stylemap
    font.os2_vendor = vendor
    font.os2_fstype = 4  # Printable Document (suitable for SF Mono)
    font.os2_family_class = 2057  # SS Typewriter Gothic
    font.os2_panose = (
        2,  # Latin: Text and Display
        11,  # Normal Sans
        style_property.panose_weight,
        9,  # Monospaced
        3,  # Contrast = Very Low
        2,  # No Variation
        2,  # Straight Arms/Horizontal
        style_property.panose_letterform,
        2,  # Midline = Standard/Trimmed
        4,  # X-height = Constant/Large
    )

    font.os2_typoascent = ascent
    font.os2_typodescent = -descent
    font.os2_typoascent_add = 0
    font.os2_typodescent_add = 0
    font.os2_typolinegap = 0

    font.os2_winascent = os2_ascent
    font.os2_windescent = os2_descent
    font.os2_winascent_add = 0
    font.os2_windescent_add = 0

    font.hhea_ascent = os2_ascent
    font.hhea_descent = -os2_descent
    font.hhea_ascent_add = 0
    font.hhea_descent_add = 0
    font.hhea_linegap = 0

    return font


def _normalize_symbol_width(
    glyph: Any, source_width: int, source_em: int, en_width: int, jp_width: int
) -> None:
    """合成元glyphの送り幅に基づき、記号の半角・全角幅を設定する."""
    if source_width == 0:
        return
    half_em = source_em / 2
    glyph.width = (
        jp_width if abs(source_width - source_em) <= abs(source_width - half_em) else en_width
    )


def _load_jp_font(
    path: Path,
    ascent: int,
    descent: int,
    em: int,
    en_width: int,
    jp_width: int,
    jp_scale_offset: float,
) -> Any:
    """JPフォントを開き、旧 main.py 相当のサイズ調整を行う."""
    font = fontforge.open(str(path))
    old_jp_ascent = font.ascent
    source_em = font.em
    source_widths = {glyph.glyphname: glyph.width for glyph in font.glyphs()}
    scale = ascent / old_jp_ascent + jp_scale_offset

    font.encoding = properties.ENCODING

    font.selection.all()
    font.unlinkReferences()
    font.ascent = ascent
    font.descent = descent
    font.em = em

    for glyph in font.glyphs():
        if not glyph.isWorthOutputting:
            font.selection.select(glyph)
            font.clear()
            continue

        glyph.transform(psMat.scale(scale, scale))

        if glyph.encoding in params.HANKAKU_KANA_LIST:
            glyph.width = en_width
        elif glyph.encoding in params.FULLWIDTH_CODES_LIST:
            glyph.width = jp_width
        elif 0 <= glyph.encoding <= 0x10FFFF:
            _normalize_symbol_width(
                glyph,
                source_width=source_widths[glyph.glyphname],
                source_em=source_em,
                en_width=en_width,
                jp_width=jp_width,
            )
    return font


def _load_en_font(path: Path) -> Any:
    """ENフォントを開く."""
    font = fontforge.open(str(path))
    font.encoding = properties.ENCODING
    return font


def _apply_jp_stroke_width(font: Any, stroke_width: int) -> None:
    """JP glyphをmerge前に少し太らせる."""
    if stroke_width == 0:
        return

    glyph_widths = [(glyph, glyph.width) for glyph in font.glyphs() if glyph.isWorthOutputting]

    font.selection.all()
    font.stroke("circular", stroke_width, "round", "round", ("removeinternal", "cleanup"))
    font.selection.none()

    for glyph, width in glyph_widths:
        glyph.width = width


def _scale_nerd_glyphs(font: Any, scales: dict[str, float]) -> None:
    """指定codepointのglyphを、advanceを変えずにink中心基準で拡大縮小する.

    公式font-patcherがv5.0.0の独自patcherより小さく埋め込むglyph
    (appleロゴなど) の補正に使う。
    """
    for key, factor in scales.items():
        start, end = parse_codepoint_range(key)
        for code in range(start, end + 1):
            try:
                glyph = font[code]
            except TypeError:
                continue
            xmin, ymin, xmax, ymax = glyph.boundingBox()
            if xmax <= xmin:
                continue
            width = glyph.width
            center_x = (xmin + xmax) / 2
            center_y = (ymin + ymax) / 2
            glyph.transform(psMat.translate(-center_x, -center_y))
            glyph.transform(psMat.scale(factor, factor))
            glyph.transform(psMat.translate(center_x, center_y))
            glyph.width = width


def _copy_unicode_mappings(base_font: Any, source_font: Any) -> None:
    """mergeFonts後、JP側のunicode/altuniを最終フォントに反映する."""
    for glyph in source_font.glyphs():
        if not glyph.isWorthOutputting:
            base_font.selection.select(glyph)
            base_font.clear()
            base_font.selection.none()
            continue
        code = glyph.unicode
        try:
            if code == -1:
                if glyph.altuni is not None:
                    base_font[glyph.glyphname].altuni = glyph.altuni
                continue
            if glyph.altuni is not None:
                base_font[code].altuni = glyph.altuni
            base_font[code].unicode = code
        except TypeError:
            pass


def build(request: BuildRequest) -> Path:
    """1つのstyleを生成し、ttfとotfを出力してttfのpathを返す."""
    cfg = request.config

    familyname = cfg.familyname_for()
    copyright_text = cfg.metadata.copyright or properties.DEFAULT_COPYRIGHT
    vendor = cfg.metadata.vendor or properties.DEFAULT_VENDOR

    base_style = properties.base_style_of(request.style)
    en_path = getattr(cfg.fonts.en, base_style.lower())
    jp_path = getattr(cfg.fonts.jp, base_style.lower())

    base_font = _new_font(
        familyname=familyname,
        style=request.style,
        italic_angle=cfg.italic_angle,
        version=request.version,
        copyright_text=copyright_text,
        vendor=vendor,
        ascent=cfg.ascent,
        descent=cfg.descent,
        em=cfg.em,
        underline_pos=cfg.underline_pos,
        underline_height=cfg.underline_height,
        os2_ascent=cfg.os2_ascent,
        os2_descent=cfg.os2_descent,
    )

    with tempfile.TemporaryDirectory(prefix="robotomonojp-") as tmpdir:
        tmp_root = Path(tmpdir)
        en_tmp = tmp_root / f"en-{request.style}.ttf"
        jp_tmp = tmp_root / f"jp-{request.style}.ttf"

        en_font = _load_en_font(en_path)
        en_font.generate(str(en_tmp))
        en_font.close()

        en_reload = fontforge.open(str(en_tmp))
        en_reload.encoding = properties.ENCODING
        base_font.mergeFonts(en_reload)
        en_reload.close()

        jp_font = _load_jp_font(
            jp_path,
            ascent=cfg.ascent,
            descent=cfg.descent,
            em=cfg.em,
            en_width=cfg.en_width,
            jp_width=cfg.jp_width,
            jp_scale_offset=cfg.jp_scale_offset,
        )
        _apply_jp_stroke_width(jp_font, cfg.jp_stroke_width)
        jp_font.generate(str(jp_tmp))
        jp_font.close()

        jp_reload = fontforge.open(str(jp_tmp))
        base_font.mergeFonts(jp_reload)
        _copy_unicode_mappings(base_font, jp_reload)
        jp_reload.close()

        base_font.selection.all()
        base_font.removeOverlap()
        base_font.round()
        base_font.autoHint()
        base_font.autoInstr()
        base_font.selection.none()

        if properties.is_italic(request.style):
            make_italic(base_font, cfg.italic_angle)
            fix_all_glyph_points(base_font, do_round=True, add_extrema=True)
        else:
            fix_all_glyph_points(base_font, add_extrema=True)

        # 最終ステージ: リガチャを削除.
        remove_glyphs_with_features(base_font, params.LIGATURE_FEATURES)
        # 旧実装で明示的に消していた FB00-FB4F のUnicodeレンジも念のため削除.
        clear_font_glyph(base_font, params.LIGATURE[0], params.LIGATURE[1])

        family_out = request.output_dir / familyname
        family_out.mkdir(parents=True, exist_ok=True)
        ttf_out = family_out / f"{familyname}-{request.style}.ttf"
        otf_out = family_out / f"{familyname}-{request.style}.otf"

        pre_patch_ttf = tmp_root / f"{familyname}-{request.style}.pre.ttf"
        base_font.generate(str(pre_patch_ttf))
        base_font.generate(str(otf_out), flags=("opentype",))
        base_font.close()

        if request.apply_nerd_font:
            patched_ttf = run_nerd_font_patch(
                pre_patch_ttf,
                tmp_root / "patched",
                nerd_fonts_root=request.nerd_fonts_root,
                complete=True,
                mono=False,
            )
            if cfg.nerd_font_glyph_scales:
                patched_font = fontforge.open(str(patched_ttf))
                _scale_nerd_glyphs(patched_font, cfg.nerd_font_glyph_scales)
                patched_font.generate(str(patched_ttf))
                patched_font.close()
            shutil.copy(patched_ttf, ttf_out)
        else:
            shutil.copy(pre_patch_ttf, ttf_out)

    return ttf_out
