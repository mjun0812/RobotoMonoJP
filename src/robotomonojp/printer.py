"""print コマンドの本体. FontForge の printSample を使って PDF を出力する."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

try:  # pragma: no cover
    import fontforge as _fontforge  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    _fontforge = None

fontforge: Any = cast(Any, _fontforge)

DEFAULT_SIZES: tuple[int, ...] = (8, 10, 12, 14, 18, 24, 36)


def print_pdf(
    font_path: Path, sample: str, output: Path, sizes: tuple[int, ...] | None = None
) -> Path:
    """指定フォントで sample を複数サイズにレンダリングしたPDFを output に書き出す.

    Args:
        font_path: 対象フォントの ttf/otf path.
        sample: レンダリングする文字列. 空文字列なら FontForge のデフォルトサンプル.
        output: 出力先PDFのpath.
        sizes: サイズリスト (pt). 未指定なら DEFAULT_SIZES.
    """
    if fontforge is None:
        raise RuntimeError("fontforge python bindings が使えません. Docker外で実行していませんか?")

    used_sizes = sizes or DEFAULT_SIZES
    output.parent.mkdir(parents=True, exist_ok=True)

    font = fontforge.open(str(font_path))
    try:
        fontforge.printSetup("pdf-file")
        # printSample は (type, pointsize, sample, outputfile) を受ける.
        # 複数サイズを重ねる方法は無いため、最大サイズをbase pointsizeにする.
        # sample が空文字列なら "fontdisplay" タイプでglyph tableを吐く.
        if not sample:
            font.printSample("fontdisplay", max(used_sizes), "", str(output))
        else:
            multi = "\n".join(f"{s}pt: {sample}" for s in used_sizes)
            font.printSample("multisize", max(used_sizes), multi, str(output))
    finally:
        font.close()

    return output
