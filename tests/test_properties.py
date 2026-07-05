"""properties module のテスト. FontForge非依存部分."""

from __future__ import annotations

from robotomonojp.properties import STYLE_PROPERTIES, STYLES, base_style_of, is_italic


def test_style_property_keys() -> None:
    assert set(STYLE_PROPERTIES.keys()) == set(STYLES)


def test_base_style_of() -> None:
    assert base_style_of("Regular") == "Regular"
    assert base_style_of("Italic") == "Regular"
    assert base_style_of("Bold") == "Bold"
    assert base_style_of("BoldItalic") == "Bold"


def test_is_italic() -> None:
    assert not is_italic("Regular")
    assert not is_italic("Bold")
    assert is_italic("Italic")
    assert is_italic("BoldItalic")
