"""print コマンドの本体. FontForge の printSample を使って PDF を出力する."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

try:  # pragma: no cover
    import fontforge as _fontforge  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    _fontforge = None

fontforge: Any = cast(Any, _fontforge)

DEFAULT_SIZE = 24


def print_pdf(font_path: Path, sample: str, output: Path, size: int | None = None) -> Path:
    """指定フォントで sample をレンダリングしたPDFを output に書き出す.

    FontForge の複数サイズ出力 ('waterfall' / 'multisize') は空のPDFを出力する
    バグがあるため、単一サイズの 'fontsample' でレンダリングする。

    Args:
        font_path: 対象フォントの ttf/otf path.
        sample: レンダリングする文字列. 空文字列なら FontForge のglyph table.
        output: 出力先PDFのpath.
        size: レンダリングサイズ (pt). 未指定なら DEFAULT_SIZE.
    """
    if fontforge is None:
        raise RuntimeError("fontforge python bindings が使えません. Docker外で実行していませんか?")

    used_size = size or DEFAULT_SIZE
    output.parent.mkdir(parents=True, exist_ok=True)

    font = fontforge.open(str(font_path))
    try:
        fontforge.printSetup("pdf-file")
        # printSample は (type, pointsize, sample, outputfile) を受ける.
        # sample が空文字列なら "fontdisplay" タイプでglyph tableを吐く.
        if not sample:
            font.printSample("fontdisplay", used_size, "", str(output))
        else:
            font.printSample("fontsample", used_size, sample, str(output))
    finally:
        font.close()

    return output
