"""eyecatch module の単体テスト."""

from __future__ import annotations

from pathlib import Path

from robotomonojp.eyecatch import generate_eyecatch

FONT = Path("fonts/RobotoMono/RobotoMono-Regular.ttf")


def test_generate_eyecatch(tmp_path: Path) -> None:
    out = generate_eyecatch(FONT, tmp_path / "eyecatch.svg")
    svg = out.read_text(encoding="utf-8")
    assert svg.startswith("<svg")
    assert 'aria-label="Roboto Mono"' in svg  # family名がタイトルになる
    assert svg.count("<path") > 50  # glyphがpath化されている
    assert 'fill="url(#title)"' in svg


def test_generate_eyecatch_custom_title(tmp_path: Path) -> None:
    out = generate_eyecatch(FONT, tmp_path / "eyecatch.svg", title="MyFont")
    assert 'aria-label="MyFont"' in out.read_text(encoding="utf-8")
