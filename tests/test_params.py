"""params module のテスト. FontForge非依存部分."""

from __future__ import annotations

from robotomonojp import params


def test_vertical_lookup_prefixes_are_preserved() -> None:
    assert "'vert'" not in params.GSUB_LOOKUP_PREFIXES
    assert "'vrt2'" not in params.GSUB_LOOKUP_PREFIXES


def test_kerning_lookup_prefixes_are_removed() -> None:
    assert "'kern'" in params.GPOS_LOOKUP_PREFIXES
    assert "'vkrn'" in params.GPOS_LOOKUP_PREFIXES
