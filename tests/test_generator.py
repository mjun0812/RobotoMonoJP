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
    font = FakeFont(ascent=880, glyph_list=[hankaku, fullwidth, latin, empty])
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
    for glyph in (hankaku, fullwidth, latin):
        assert glyph.transforms == [("scale", expected_scale, expected_scale)]

    assert hankaku.width == 1299
    assert fullwidth.width == 1849
    assert latin.width == 500  # 半角カナ・全角以外は幅を触らない

    assert empty.transforms == []
    assert font.selection.selected == [empty]
    assert font.cleared == 1


class FakeIndexableFont:
    """codepoint indexing だけを持つ font fake."""

    def __init__(self, glyph_map: dict[int, FakeGlyph]) -> None:
        """codepoint → glyph のマップを設定する."""
        self._glyphs = glyph_map

    def __getitem__(self, code: int) -> FakeGlyph:
        """fontforge と同じく、存在しない codepoint は TypeError."""
        if code not in self._glyphs:
            raise TypeError(f"no glyph at {code}")
        return self._glyphs[code]


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
