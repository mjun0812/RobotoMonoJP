"""preview module の単体テスト."""

from __future__ import annotations

from pathlib import Path

from robotomonojp.preview import generate_preview

FONT = Path("fonts/RobotoMono/RobotoMono-Regular.ttf")


def test_generate_preview(tmp_path: Path) -> None:
    """指定フォントを参照する静的HTMLを生成する."""
    out = generate_preview(FONT, tmp_path / "preview.html")
    html = out.read_text(encoding="utf-8")

    assert html.startswith("<!doctype html>")
    assert "<title>Roboto Mono preview</title>" in html
    assert "@font-face {" in html
    assert 'font-family: "RobotoMonoJPPreview";' in html
    assert "RobotoMono-Regular.ttf" in html
    assert "ABC日本語abc123" in html
    assert "半角: A B C D" in html
    assert "全角: A　B　C　D" in html


def test_generate_preview_custom_title(tmp_path: Path) -> None:
    """title を指定するとページタイトルと見出しに使われる."""
    out = generate_preview(FONT, tmp_path / "preview.html", title="My Preview")
    html = out.read_text(encoding="utf-8")

    assert "<title>My Preview preview</title>" in html
    assert "<h1>My Preview</h1>" in html
