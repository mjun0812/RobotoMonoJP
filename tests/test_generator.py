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

    def __init__(self, ascent: int, glyph_list: list[FakeGlyph]) -> None:
        """元フォントの ascent と glyph 一覧を設定する."""
        self.ascent = ascent
        self.descent = 0
        self.em = 0
        self.encoding = ""
        self.selection = FakeSelection()
        self.cleared = 0
        self._glyphs = glyph_list

    def unlinkReferences(self) -> None:
        """参照解除 (何もしない)."""

    def clear(self) -> None:
        """選択中 glyph の削除回数を記録する."""
        self.cleared += 1

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
    ambiguous = FakeGlyph(0x25CB)  # ○ (East Asian Width = A)
    ambiguous.width = 1961
    ambiguous.bbox = (143.0, -20.0, 1818.0, 1500.0)
    narrow_symbol = FakeGlyph(0x2502)  # │ (inkがセル幅に収まる記号)
    narrow_symbol.width = 1961
    narrow_symbol.bbox = (700.0, 0.0, 900.0, 1200.0)
    wide_symbol = FakeGlyph(0x3007)  # 〇 (East Asian Width = W)
    wide_symbol.width = 1961
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
    for glyph in (hankaku, fullwidth, latin, wide_symbol, zero_width):
        assert glyph.transforms == [("scale", expected_scale, expected_scale)]

    assert hankaku.width == 1299
    assert fullwidth.width == 1849
    assert latin.width == 1299  # 曖昧幅・中立の記号は半角セルに正規化する

    # 曖昧幅 (EAW=A) でinkがはみ出すglyphは、ink基準で縮小して中央に寄せる.
    shrink = (1299 * generator.SYMBOL_INK_RATIO) / (1818.0 - 143.0)
    dx = (1299 - 143.0 * shrink - 1818.0 * shrink) / 2
    assert ambiguous.transforms == [
        ("scale", expected_scale, expected_scale),
        ("scale", shrink, shrink),
        ("translate", dx, 0),
    ]
    assert ambiguous.width == 1299

    # inkがセル幅に収まる記号は縮小せず、中央寄せだけ行う.
    assert narrow_symbol.transforms == [
        ("scale", expected_scale, expected_scale),
        ("translate", (1299 - 700.0 - 900.0) / 2, 0),
    ]
    assert narrow_symbol.width == 1299

    # EAW=W の記号は jp_width、zero-widthのglyphは幅を触らない.
    assert wide_symbol.width == 1849
    assert zero_width.width == 0

    assert empty.transforms == []
    assert font.selection.selected == [empty]
    assert font.cleared == 1
