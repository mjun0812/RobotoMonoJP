from pathlib import Path

from fontTools.ttLib import TTFont


REGULAR_FONT = Path("RobotoMonoJP/RobotoMonoJP-Regular.ttf")
MONO_FONT = Path("RobotoMonoJP-Mono/RobotoMonoJP-Mono-Regular.ttf")

REGULAR_HALF_WIDTH = 1299
REGULAR_FULL_WIDTH = 1849
MONO_HALF_WIDTH = 1024
MONO_FULL_WIDTH = 2048

REGULAR_EXPECTED_WIDTHS = {
    "→": REGULAR_HALF_WIDTH,
    "○": REGULAR_HALF_WIDTH,
    "♥": REGULAR_HALF_WIDTH,
    "ｱ": REGULAR_HALF_WIDTH,
    "｡": REGULAR_HALF_WIDTH,
    "あ": REGULAR_FULL_WIDTH,
    "漢": REGULAR_FULL_WIDTH,
    "Ａ": REGULAR_FULL_WIDTH,
    "。": REGULAR_FULL_WIDTH,
    "￥": REGULAR_FULL_WIDTH,
    "（": REGULAR_FULL_WIDTH,
}

MONO_EXPECTED_WIDTHS = {
    "A": MONO_HALF_WIDTH,
    "→": MONO_HALF_WIDTH,
    "○": MONO_HALF_WIDTH,
    "─": MONO_HALF_WIDTH,
    "━": MONO_HALF_WIDTH,
    "♥": MONO_HALF_WIDTH,
    "ｱ": MONO_HALF_WIDTH,
    "｡": MONO_HALF_WIDTH,
    "あ": MONO_FULL_WIDTH,
    "漢": MONO_FULL_WIDTH,
    "Ａ": MONO_FULL_WIDTH,
    "。": MONO_FULL_WIDTH,
    "￥": MONO_FULL_WIDTH,
    "（": MONO_FULL_WIDTH,
}


def get_cmap(font: TTFont) -> dict[int, str]:
    """Return a Unicode code point to glyph name map.

    Args:
        font: FontTools TTFont.

    Returns:
        Mapping from Unicode code points to glyph names.
    """
    cmap: dict[int, str] = {}
    for table in font["cmap"].tables:
        cmap.update(table.cmap)
    return cmap


def check_widths(font_path: Path, expected_widths: dict[str, int]) -> list[str]:
    """Check glyph advance widths.

    Args:
        font_path: Font file path.
        expected_widths: Mapping from character to expected advance width.

    Returns:
        Error messages. An empty list means all checks passed.
    """
    errors: list[str] = []
    font = TTFont(font_path)
    cmap = get_cmap(font)
    metrics = font["hmtx"].metrics

    for char, expected_width in expected_widths.items():
        code = ord(char)
        glyph_name = cmap.get(code)
        if glyph_name is None:
            errors.append(f"{font_path}: {char} U+{code:04X} is missing")
            continue

        actual_width, _left_side_bearing = metrics[glyph_name]
        if actual_width != expected_width:
            errors.append(
                f"{font_path}: {char} U+{code:04X} width is "
                f"{actual_width}, expected {expected_width}"
            )

    font.close()
    return errors


def main() -> int:
    """Run font metric checks.

    Returns:
        Process exit code.
    """
    errors = check_widths(REGULAR_FONT, REGULAR_EXPECTED_WIDTHS) + check_widths(
        MONO_FONT, MONO_EXPECTED_WIDTHS
    )
    if errors:
        for error in errors:
            print(error)
        return 1

    print("font metrics are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
