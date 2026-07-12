"""generator module の単体テスト."""

from __future__ import annotations

from pathlib import Path

import pytest

from robotomonojp import generator, properties


class FakeSelection:
    """font.selection の最小 fake."""

    def __init__(self) -> None:
        """選択操作の記録を初期化する."""
        self.selected: list[object] = []

    def all(self) -> None:
        """全選択 (何もしない)."""

    def none(self) -> None:
        """選択解除 (何もしない)."""

    def select(self, glyph: object) -> None:
        """glyph の選択を記録する."""
        self.selected.append(glyph)


class FakeGlyph:
    """encoding と width を持つ glyph fake."""

    def __init__(self, encoding: int, *, worth_outputting: bool = True) -> None:
        """初期状態の glyph を作る."""
        self.encoding = encoding
        self.glyphname = f"uni{encoding:04X}"
        self.unicode = encoding
        self.altuni: tuple[tuple[int, int, int], ...] | None = None
        self.width = 500
        self.bbox = (0.0, 0.0, 0.0, 0.0)
        self.isWorthOutputting = worth_outputting
        self.transforms: list[object] = []

    def transform(self, matrix: object) -> None:
        """適用された変換行列を記録する."""
        self.transforms.append(matrix)

    def boundingBox(self) -> tuple[float, float, float, float]:
        """ink の bbox (xmin, ymin, xmax, ymax) を返す."""
        return self.bbox


class FakeFont:
    """fontforge.font の最小 fake."""

    def __init__(self, ascent: int, glyph_list: list[FakeGlyph], *, em: int = 1000) -> None:
        """元フォントの ascent と glyph 一覧を設定する."""
        self.ascent = ascent
        self.descent = 0
        self.em = em
        self._encoding = ""
        self.selection = FakeSelection()
        self.cleared = 0
        self.overlap_removed = 0
        self.strokes: list[tuple[object, ...]] = []
        self._glyphs = glyph_list
        self.reencoded_codepoints: dict[str, int] = {}

    @property
    def encoding(self) -> str:
        """現在のencoding名を返す."""
        return self._encoding

    @encoding.setter
    def encoding(self, value: str) -> None:
        """encoding変更時のcodepoint再割り当てを再現する."""
        self._encoding = value
        for glyph in self._glyphs:
            if glyph.glyphname in self.reencoded_codepoints:
                glyph.encoding = self.reencoded_codepoints[glyph.glyphname]

    def unlinkReferences(self) -> None:
        """参照解除 (何もしない)."""

    def clear(self) -> None:
        """選択中 glyph の削除回数を記録する."""
        self.cleared += 1

    def stroke(self, *args: object) -> None:
        """stroke の呼び出しを記録する."""
        self.strokes.append(args)

    def removeOverlap(self) -> None:
        """overlap 削除の呼び出し回数を記録する."""
        self.overlap_removed += 1

    def glyphs(self) -> list[FakeGlyph]:
        """glyph 一覧を返す."""
        return self._glyphs


class FakeFontForge:
    """fontforge module の最小 fake."""

    opened: FakeFont

    @staticmethod
    def open(path: str) -> FakeFont:
        """fontforge.open の代わりに fake font を返す."""
        return FakeFontForge.opened


class FakePsMat:
    """psMat module の最小 fake."""

    @staticmethod
    def scale(x: float, y: float) -> tuple[str, float, float]:
        """スケール行列の代わりにタプルを返す."""
        return ("scale", x, y)

    @staticmethod
    def translate(x: float, y: float) -> tuple[str, float, float]:
        """平行移動行列の代わりにタプルを返す."""
        return ("translate", x, y)


def test_load_en_font_keeps_source_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """ENフォントは開いたあと encoding 以外を変更しない."""
    FakeFontForge.opened = FakeFont(ascent=1638, glyph_list=[])
    monkeypatch.setattr(generator, "fontforge", FakeFontForge)

    font = generator._load_en_font(Path("RobotoMono-Regular.ttf"))

    assert font is FakeFontForge.opened
    assert font.encoding == properties.ENCODING
    assert font.ascent == 1638
    assert all(glyph.transforms == [] for glyph in font.glyphs())


def test_load_jp_font_applies_old_proportional_scale(monkeypatch: pytest.MonkeyPatch) -> None:
    """JPフォントは旧 main.py と同じ ascent 比 + offset でスケールする."""
    hankaku = FakeGlyph(0xFF61)
    fullwidth = FakeGlyph(0x3042)
    latin = FakeGlyph(0x0041)
    empty = FakeGlyph(0x0000, worth_outputting=False)
    ambiguous = FakeGlyph(0x1234)
    ambiguous.width = 1000
    ambiguous.bbox = (143.0, -20.0, 1818.0, 1500.0)
    narrow_symbol = FakeGlyph(0x2502)  # │ (inkがセル幅に収まる記号)
    narrow_symbol.width = 500
    narrow_symbol.bbox = (700.0, 0.0, 900.0, 1200.0)
    wide_symbol = FakeGlyph(0x3007)  # 〇 (East Asian Width = W)
    wide_symbol.width = 1000
    zero_width = FakeGlyph(0x0300)  # combining mark
    zero_width.width = 0
    font = FakeFont(
        ascent=880,
        glyph_list=[
            hankaku,
            fullwidth,
            latin,
            empty,
            ambiguous,
            narrow_symbol,
            wide_symbol,
            zero_width,
        ],
    )
    font.reencoded_codepoints[ambiguous.glyphname] = 0x25CB
    FakeFontForge.opened = font
    monkeypatch.setattr(generator, "fontforge", FakeFontForge)
    monkeypatch.setattr(generator, "psMat", FakePsMat)

    result = generator._load_jp_font(
        Path("IBMPlexSansJP-Regular.ttf"),
        ascent=1638,
        descent=410,
        em=2048,
        en_width=1299,
        jp_width=1849,
        jp_scale_offset=0.10,
    )

    assert result is font
    assert font.encoding == properties.ENCODING
    assert (font.ascent, font.descent, font.em) == (1638, 410, 2048)

    expected_scale = 1638 / 880 + 0.10
    for glyph in (hankaku, fullwidth, latin, ambiguous, narrow_symbol, wide_symbol, zero_width):
        assert glyph.transforms == [("scale", expected_scale, expected_scale)]

    assert hankaku.width == 1299
    assert fullwidth.width == 1849
    assert latin.width == 1299  # 元フォントで半角のglyphは半角セルに正規化する

    # 元フォントで全角の曖昧幅文字は、字形を縮小せず全角幅を維持する.
    assert ambiguous.width == 1849

    # 元フォントで半角の記号は縮小せず、半角幅を設定する.
    assert narrow_symbol.transforms == [("scale", expected_scale, expected_scale)]
    assert narrow_symbol.width == 1299

    # 元フォントで全角の記号は jp_width、zero-widthのglyphは幅を触らない.
    assert wide_symbol.width == 1849
    assert zero_width.width == 0

    assert empty.transforms == []
    assert font.selection.selected == [empty]
    assert font.cleared == 1


def test_apply_jp_stroke_width_keeps_advance_widths() -> None:
    """JP stroke補正は輪郭だけを太らせ、advance widthを維持する."""
    fullwidth = FakeGlyph(0x3042)
    fullwidth.width = 1849
    hankaku = FakeGlyph(0xFF61)
    hankaku.width = 1299
    empty = FakeGlyph(0x0000, worth_outputting=False)
    empty.width = 500
    font = FakeFont(ascent=1638, glyph_list=[fullwidth, hankaku, empty])

    generator._apply_jp_stroke_width(font, 8)

    assert font.strokes == [("circular", 8, "round", "round", ("removeinternal", "cleanup"))]
    assert font.overlap_removed == 0
    assert fullwidth.width == 1849
    assert hankaku.width == 1299
    assert empty.width == 500


def test_apply_jp_stroke_width_skips_zero() -> None:
    """stroke幅0では何もしない."""
    glyph = FakeGlyph(0x3042)
    font = FakeFont(ascent=1638, glyph_list=[glyph])

    generator._apply_jp_stroke_width(font, 0)

    assert font.strokes == []
    assert font.overlap_removed == 0


def test_normalize_ambiguous_symbol_for_mono(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mono版では全角の曖昧幅glyphを半角セルへ縮小する."""
    glyph = FakeGlyph(0x25CB)
    monkeypatch.setattr(generator, "psMat", FakePsMat)

    generator._normalize_symbol_width(
        glyph,
        source_width=1000,
        source_em=1000,
        en_width=1299,
        jp_width=1849,
        mono=True,
    )

    assert glyph.transforms == [("scale", 1299 / 1849, 1)]
    assert glyph.width == 1299


class FakeIndexableFont:
    """codepoint indexing だけを持つ font fake."""

    def __init__(self, glyph_map: dict[int | str, FakeGlyph]) -> None:
        """codepoint → glyph のマップを設定する."""
        self._glyphs = glyph_map

    def __getitem__(self, code: int | str) -> FakeGlyph:
        """fontforge と同じく、存在しない codepoint は TypeError."""
        if code not in self._glyphs:
            raise TypeError(f"no glyph at {code}")
        return self._glyphs[code]


class FakeMappingFont(FakeIndexableFont):
    """unicode mapping のコピーに必要な操作を持つ font fake."""

    def __init__(self, glyph_map: dict[int | str, FakeGlyph]) -> None:
        """glyph map と selection を設定する."""
        super().__init__(glyph_map)
        self.selection = FakeSelection()
        self.cleared = 0

    def glyphs(self) -> list[FakeGlyph]:
        """全glyphを返す."""
        return list(self._glyphs.values())

    def clear(self) -> None:
        """glyph削除の呼び出し回数を記録する."""
        self.cleared += 1


def test_copy_unicode_mappings_keeps_variation_sequences() -> None:
    """JP側のIVS mappingを最終フォントへ引き継ぐ."""
    codepoint = 0x9089
    variation_selector = 0xE0101
    source_glyph = FakeGlyph(codepoint)
    source_glyph.altuni = ((codepoint, variation_selector, 0),)
    source_variant = FakeGlyph(-1)
    source_variant.unicode = -1
    source_variant.glyphname = "uni9089.aalt"
    source_variant.altuni = ((codepoint, variation_selector + 1, 0),)
    target_glyph = FakeGlyph(codepoint)
    target_variant = FakeGlyph(-1)
    target_variant.unicode = -1
    target_variant.glyphname = source_variant.glyphname
    source = FakeMappingFont({codepoint: source_glyph, source_variant.glyphname: source_variant})
    target = FakeMappingFont({codepoint: target_glyph, target_variant.glyphname: target_variant})

    generator._copy_unicode_mappings(target, source)

    assert target_glyph.unicode == codepoint
    assert target_glyph.altuni == ((codepoint, variation_selector, 0),)
    assert target_variant.altuni == ((codepoint, variation_selector + 1, 0),)


def test_scale_nerd_glyphs(monkeypatch: pytest.MonkeyPatch) -> None:
    """指定codepointのglyphだけをink中心基準で拡大する."""
    apple = FakeGlyph(0xF179)
    apple.bbox = (100.0, 0.0, 1300.0, 1600.0)
    other = FakeGlyph(0xF126)
    empty_ink = FakeGlyph(0xF17A)  # inkが無いglyphは触らない
    font = FakeIndexableFont({0xF179: apple, 0xF126: other, 0xF17A: empty_ink})
    monkeypatch.setattr(generator, "psMat", FakePsMat)

    # 存在しない F17B を含むレンジ指定でもエラーにならない.
    generator._scale_nerd_glyphs(font, {"F179-F17B": 1.15})

    center_x = (100.0 + 1300.0) / 2
    center_y = (0.0 + 1600.0) / 2
    assert apple.transforms == [
        ("translate", -center_x, -center_y),
        ("scale", 1.15, 1.15),
        ("translate", center_x, center_y),
    ]
    assert empty_ink.transforms == []
    assert other.transforms == []  # レンジ外は触らない
