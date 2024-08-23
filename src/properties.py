from dataclasses import dataclass
from typing import Literal


@dataclass
class StyleProperty:
    weight: Literal["Book", "Bold"]
    os2_weight: int
    os2_stylemap: int
    panose_weight: int
    panose_letterform: int


COPYRIGHT = """
[IBM Plex]
Copyright © 2017 IBM Corp.
[RobotoMono]
Copyright 2015 The Roboto Mono Project.
[Nerd Fonts]
Copyright (c) 2014, Ryan L McIntyre
[RobotoMonoJP]
Copyright (c) 2021 Junya Morioka
"""

VERSION = "5.0.0"
ENCODING = "UnicodeFull"
FAMILYNAME = "RobotoMonoJP"

# ### サイズ関係 ###
ASCENT = 1638  # 上方向の最大値
DESCENT = 410  # 下方向の最大値
EM = ASCENT + DESCENT
UNDERLINE_POS = -200
UNDERLINE_HEIGHT = 100
ITALIC_ANGLE = -11

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
    "RegularItalic": StyleProperty(
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
