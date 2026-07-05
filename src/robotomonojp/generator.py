"""フォント合成のコアロジック. 旧 main_mono.py / main.py 相当."""

from __future__ import annotations

import contextlib
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from . import params, properties
from .config import Config, VariantConfig
from .fontforge_helpers import (
    clear_font_glyph,
    fix_all_glyph_points,
    fontforge,
    make_italic,
    remove_glyphs_with_features,
    remove_lookups,
    resize_all_glyph_width,
    resize_all_scale,
    resize_glyph_width,
    set_font_em,
)
from .patcher import DEFAULT_NERD_FONTS_ROOT
from .patcher import patch as run_nerd_font_patch


@dataclass(frozen=True)
class BuildRequest:
    """generate1回分の入力."""

    config: Config
    variant_name: str  # "proportional" | "mono"
    style: str  # "Regular" | "Bold" | "Italic" | "BoldItalic"
    version: str
    output_dir: Path
    apply_nerd_font: bool = True
    nerd_fonts_root: Path = DEFAULT_NERD_FONTS_ROOT


def _new_font(
    familyname: str,
    style: str,
    variant_cfg: VariantConfig,
    italic_angle: float,
    version: str,
    copyright_text: str,
    vendor: str,
) -> Any:
    """空フォントを作り、メタデータとOS/2/hheaを埋める."""
    font = fontforge.font()
    style_property = properties.STYLE_PROPERTIES[style]

    font.ascent = variant_cfg.ascent
    font.descent = variant_cfg.descent
    font.em = variant_cfg.em
    font.italicangle = italic_angle if properties.is_italic(style) else 0
    font.upos = variant_cfg.underline_pos
    font.uwidth = variant_cfg.underline_height
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

    font.os2_typoascent = variant_cfg.ascent
    font.os2_typodescent = -variant_cfg.descent
    font.os2_typoascent_add = 0
    font.os2_typodescent_add = 0
    font.os2_typolinegap = 0

    font.os2_winascent = variant_cfg.os2_ascent
    font.os2_windescent = variant_cfg.os2_descent
    font.os2_winascent_add = 0
    font.os2_windescent_add = 0

    font.hhea_ascent = variant_cfg.os2_ascent
    font.hhea_descent = -variant_cfg.os2_descent
    font.hhea_ascent_add = 0
    font.hhea_descent_add = 0
    font.hhea_linegap = 0

    return font


def _load_jp_font(path: Path, variant_cfg: VariantConfig) -> Any:
    """JPフォントを開き、旧 main_mono.get_jp_font 相当の前処理を行う."""
    font = fontforge.open(str(path))
    font.encoding = properties.ENCODING

    remove_lookups(
        font,
        gsub_prefixes=params.GSUB_LOOKUP_PREFIXES,
        gpos_prefixes=params.GPOS_LOOKUP_PREFIXES,
    )

    clear_font_glyph(font, params.LIGATURE[0], params.LIGATURE[1])

    for start, end in params.JP_CLEAR_RANGES:
        clear_font_glyph(font, start, end)

    set_font_em(font, variant_cfg.ascent, variant_cfg.descent, variant_cfg.em)

    half_width = variant_cfg.em // 2
    for code in params.JP_SHRINK_TO_HALF_UNICODE:
        with contextlib.suppress(TypeError):
            resize_glyph_width(font[code], half_width)
    for name in params.JP_SHRINK_TO_HALF_GLYPHS:
        with contextlib.suppress(TypeError):
            resize_glyph_width(font[name], half_width)
    for name in params.JP_KEEP_FULLWIDTH_GLYPHS:
        with contextlib.suppress(TypeError):
            resize_glyph_width(font[name], variant_cfg.em)

    resize_all_scale(
        font,
        variant_cfg.jp_scale,
        full_width=variant_cfg.jp_width,
        half_width=variant_cfg.en_width,
    )
    fix_all_glyph_points(font, do_round=True)

    font.selection.all()
    font.unlinkReferences()
    font.selection.none()

    return font


def _load_en_font(path: Path, variant_cfg: VariantConfig) -> Any:
    """ENフォントを開き、EM/幅を variant に揃える."""
    font = fontforge.open(str(path))
    font.encoding = properties.ENCODING
    set_font_em(font, variant_cfg.ascent, variant_cfg.descent, variant_cfg.em)
    resize_all_glyph_width(font, variant_cfg.en_width)
    fix_all_glyph_points(font, do_round=True)
    return font


def _copy_unicode_mappings(base_font: Any, source_font: Any) -> None:
    """mergeFonts後、JP側のunicode/altuniを最終フォントに反映する."""
    for glyph in source_font.glyphs():
        if not glyph.isWorthOutputting:
            base_font.selection.select(glyph)
            base_font.clear()
            base_font.selection.none()
            continue
        code = glyph.unicode
        if code == -1:
            continue
        try:
            if glyph.altuni is not None:
                base_font[code].altuni = glyph.altuni
            base_font[code].unicode = code
        except TypeError:
            pass


def build(request: BuildRequest) -> Path:
    """1つの (variant, style) を生成し、ttfとotfを出力してttfのpathを返す."""
    cfg = request.config
    variant_cfg = getattr(cfg.variants, request.variant_name)
    if variant_cfg is None:
        raise ValueError(f"variant {request.variant_name!r} is not configured")

    familyname = cfg.familyname_for(request.variant_name)
    copyright_text = cfg.metadata.copyright or properties.DEFAULT_COPYRIGHT
    vendor = cfg.metadata.vendor or properties.DEFAULT_VENDOR

    base_style = properties.base_style_of(request.style)
    en_path = getattr(cfg.fonts.en, base_style.lower())
    jp_path = getattr(cfg.fonts.jp, base_style.lower())

    base_font = _new_font(
        familyname=familyname,
        style=request.style,
        variant_cfg=variant_cfg,
        italic_angle=cfg.italic_angle,
        version=request.version,
        copyright_text=copyright_text,
        vendor=vendor,
    )

    with tempfile.TemporaryDirectory(prefix="robotomonojp-") as tmpdir:
        tmp_root = Path(tmpdir)
        en_tmp = tmp_root / f"en-{request.variant_name}.ttf"
        jp_tmp = tmp_root / f"jp-{request.variant_name}.ttf"

        en_font = _load_en_font(en_path, variant_cfg)
        en_font.generate(str(en_tmp))
        en_font.close()

        en_reload = fontforge.open(str(en_tmp))
        en_reload.encoding = properties.ENCODING
        base_font.mergeFonts(en_reload)
        en_reload.close()

        jp_font = _load_jp_font(jp_path, variant_cfg)
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

        variant_out = request.output_dir / familyname
        variant_out.mkdir(parents=True, exist_ok=True)
        ttf_out = variant_out / f"{familyname}-{request.style}.ttf"
        otf_out = variant_out / f"{familyname}-{request.style}.otf"

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
            shutil.copy(patched_ttf, ttf_out)
        else:
            shutil.copy(pre_patch_ttf, ttf_out)

    return ttf_out
