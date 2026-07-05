"""JP側のglyph削除・分類に使う定数群. 旧 src/params.py を移植."""

from __future__ import annotations

# refer: https://www.asahi-net.or.jp/~ax2s-kmtn/ref/unicode/index_u.html

ASCII_SYMBOLS: tuple[int, int] = (0x0021, 0x002F)
ASCII_NUMBERS: tuple[int, int] = (0x0030, 0x0039)
ASCII_SYMBOLS_2: tuple[int, int] = (0x003A, 0x0040)
ALPHABET: tuple[int, int] = (0x0041, 0x005A)
OTHER_GLYPHS: tuple[int, int] = (0x005B, 0x2044)

LIGATURE: tuple[int, int] = (0xFB00, 0xFB4F)

HANKAKU_KANA_LIST: list[int] = list(range(0xFF61, 0xFF9F))

_FULLWIDTH_HIRAGANA_KATAKANA_LIST: list[int] = list(range(0x3040, 0x30FF))
_FULLWIDTH_CJK_UNIFIED_LIST: list[int] = list(range(0x4E00, 0x9FCF))
_FULLWIDTH_CJK_COMPATI_LIST: list[int] = list(range(0xF900, 0xFAFF))
_FULLWIDTH_CJK_UNIFIED_EX_A_LIST: list[int] = list(range(0x3400, 0x4DBF))
_FULLWIDTH_CJK_UNIFIED_EX_B_LIST: list[int] = list(range(0x20000, 0x2A6DF))
_FULLWIDTH_CJK_UNIFIED_EX_C_LIST: list[int] = list(range(0x2A700, 0x2B73F))
_FULLWIDTH_CJK_UNIFIED_EX_D_LIST: list[int] = list(range(0x2B740, 0x2B81F))
_FULLWIDTH_CJK_COMPATI_SUPP_LIST: list[int] = list(range(0x2F800, 0x2FA1F))

FULLWIDTH_CODES_LIST: list[int] = (
    _FULLWIDTH_HIRAGANA_KATAKANA_LIST
    + _FULLWIDTH_CJK_UNIFIED_LIST
    + _FULLWIDTH_CJK_COMPATI_LIST
    + _FULLWIDTH_CJK_UNIFIED_EX_A_LIST
    + _FULLWIDTH_CJK_UNIFIED_EX_B_LIST
    + _FULLWIDTH_CJK_UNIFIED_EX_C_LIST
    + _FULLWIDTH_CJK_UNIFIED_EX_D_LIST
    + _FULLWIDTH_CJK_COMPATI_SUPP_LIST
)

LIGA_RANGE: list[int] = list(range(0xFB00, 0xFB4F + 1))

# 旧 main_mono.py で JP から削除している個別コードポイント/範囲.
JP_CLEAR_RANGES: list[tuple[int, int]] = [
    ASCII_SYMBOLS,
    ASCII_NUMBERS,
    ASCII_SYMBOLS_2,
    ALPHABET,
    OTHER_GLYPHS,
    (0x20AC, 0x20AC),  # €
    (0x2190, 0x21F5),  # arrow
    (0x2200, 0x22A5),  # math symbol
    (0x2116, 0x2116),  # №
    (0x2122, 0x2122),  # ™
    (0x23A7, 0x23AD),  # curly bracket
    (0x2500, 0x2595),  # border symbol
    (0x25A0, 0x25EF),  # block symbol
]

# 旧 main_mono.py で JP の半角化 (EM // 2) 対象にしている個別glyph.
JP_SHRINK_TO_HALF_UNICODE: list[int] = [
    0x2103,  # ℃
    0x2109,  # ℉
    0x2121,  # ℡
    0x212B,  # Å
]

# glyph名指定で幅を EM // 2 に揃えるglyph.
JP_SHRINK_TO_HALF_GLYPHS: list[str] = [
    "section",
    "dagger.prop",
    "daggerdbl.prop",
    "paragraph",
    "degree",
    "plusminus",
    "multiply",
    "divide",
    "zero.zero",
    "uni51F0",
    "a.alt01",
    "g.alt01",
    "g.alt02",
    "zero.alt01",
]

# glyph名指定で幅を EM に揃えるglyph.
JP_KEEP_FULLWIDTH_GLYPHS: list[str] = [
    "perthousand.full",
    "uni51F0",
]

# 削除対象の GSUB lookup prefix. 縦書き feature (vert/vrt2) は残す.
GSUB_LOOKUP_PREFIXES: tuple[str, ...] = ("'liga'",)

# 削除対象の GPOS lookup prefix.
GPOS_LOOKUP_PREFIXES: tuple[str, ...] = (
    "'halt'",
    "'vhal'",
    "'kern'",
    "'vkrn'",
    "'palt'",
    "'vpal'",
)

# 最終フォントから削除する OpenType feature (リガチャ関連).
LIGATURE_FEATURES: tuple[str, ...] = (
    "liga",
    "dlig",
    "clig",
    "hlig",
    "calt",
)
