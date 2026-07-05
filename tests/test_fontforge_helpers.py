"""fontforge_helpers module の FontForge 非依存テスト."""

from __future__ import annotations

from robotomonojp import fontforge_helpers


class FakeGlyph:
    """幅と transform 呼び出しを記録する glyph."""

    def __init__(self, width: int) -> None:
        """初期幅を設定する."""
        self.width = width
        self.transforms: list[object] = []

    def transform(self, matrix: object) -> None:
        """適用された変換を記録する."""
        self.transforms.append(matrix)


class FakeFont:
    """em と glyph 一覧だけを持つ font."""

    def __init__(self, em: int, glyphs: list[FakeGlyph]) -> None:
        """em と glyph 一覧を設定する."""
        self.em = em
        self._glyphs = glyphs

    def glyphs(self) -> list[FakeGlyph]:
        """glyph 一覧を返す."""
        return self._glyphs


class FakePsMat:
    """psMat の最小 fake."""

    @staticmethod
    def scale(scale: float, y_scale: float | None = None) -> tuple[str, float, float | None]:
        """scale matrix の代替値を返す."""
        return ("scale", scale, y_scale)

    @staticmethod
    def translate(x: float, y: float = 0) -> tuple[str, float, float]:
        """translate matrix の代替値を返す."""
        return ("translate", x, y)

    @staticmethod
    def compose(first: object, second: object) -> tuple[str, object, object]:
        """compose matrix の代替値を返す."""
        return ("compose", first, second)


def test_resize_all_scale_sets_variant_widths(monkeypatch: object) -> None:
    """JP glyph の full/half width を variant 設定値に合わせる."""
    glyphs = [FakeGlyph(2048), FakeGlyph(1024), FakeGlyph(777)]
    font = FakeFont(2048, glyphs)
    monkeypatch.setattr(fontforge_helpers, "psMat", FakePsMat)

    fontforge_helpers.resize_all_scale(font, 0.9, full_width=1849, half_width=1299)

    assert glyphs[0].width == 1849
    assert glyphs[1].width == 1299
    assert glyphs[2].width == 777
    assert len(glyphs[0].transforms) == 1
    assert len(glyphs[1].transforms) == 1
    assert glyphs[2].transforms == []
