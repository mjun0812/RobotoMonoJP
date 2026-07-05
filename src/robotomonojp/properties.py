"""フォント/OS2/panoseに関するデフォルト定数."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DEFAULT_COPYRIGHT = """
[IBM Plex]
Copyright © 2017 IBM Corp.
[RobotoMono]
Copyright 2015 The Roboto Mono Project.
[Nerd Fonts]
Copyright (c) 2014, Ryan L McIntyre
[RobotoMonoJP]
Copyright (c) 2021 Junya Morioka
""".strip()

DEFAULT_VENDOR = "mjun"
ENCODING = "UnicodeFull"


@dataclass(frozen=True)
class StyleProperty:
    """4スタイルそれぞれの重み/panose属性."""

    weight: Literal["Book", "Bold"]
    os2_weight: int
    os2_stylemap: int
    panose_weight: int
    panose_letterform: int


STYLE_PROPERTIES: dict[str, StyleProperty] = {
    "Regular": StyleProperty(
        weight="Book",
        os2_weight=400,
        os2_stylemap=64,
        panose_weight=5,
        panose_letterform=2,
    ),
    "Bold": StyleProperty(
        weight="Bold",
        os2_weight=700,
        os2_stylemap=32,
        panose_weight=8,
        panose_letterform=2,
    ),
    "Italic": StyleProperty(
        weight="Book",
        os2_weight=400,
        os2_stylemap=1,
        panose_weight=5,
        panose_letterform=9,
    ),
    "BoldItalic": StyleProperty(
        weight="Bold",
        os2_weight=700,
        os2_stylemap=33,
        panose_weight=8,
        panose_letterform=9,
    ),
}

STYLES: tuple[str, ...] = ("Regular", "Bold", "Italic", "BoldItalic")


def base_style_of(style: str) -> Literal["Regular", "Bold"]:
    """Italic/BoldItalicはそれぞれRegular/Boldから合成する."""
    return "Bold" if "Bold" in style else "Regular"


def is_italic(style: str) -> bool:
    return "Italic" in style
