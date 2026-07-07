"""config.yaml パーサのバリデーションテスト."""

from __future__ import annotations

from pathlib import Path

import pytest

from robotomonojp.config import Config, load_config, parse_codepoint_range

VALID_MINIMAL: dict[str, object] = {
    "jp_identifier": "Plex",
    "fonts": {
        "en": {"regular": "en-r.ttf", "bold": "en-b.ttf"},
        "jp": {"regular": "jp-r.ttf", "bold": "jp-b.ttf"},
    },
    "ascent": 1638,
    "descent": 410,
    "em": 2048,
    "en_width": 1024,
    "jp_width": 2048,
    "jp_scale_offset": 0.10,
    "underline_pos": -200,
    "underline_height": 100,
    "os2_ascent": 1638,
    "os2_descent": 410,
}


def test_valid_minimal_config() -> None:
    cfg = Config.model_validate(VALID_MINIMAL)
    assert cfg.jp_identifier == "Plex"


def test_familyname_override() -> None:
    data = dict(VALID_MINIMAL)
    data["familyname"] = "MyMono"
    cfg = Config.model_validate(data)
    assert cfg.familyname_for() == "MyMono"


@pytest.mark.parametrize(
    "identifier",
    ["plex", "PLEX!", "12Plex", "AVeryLongNameThatExceedsSixteenChars", "Mono", ""],
)
def test_invalid_jp_identifier(identifier: str) -> None:
    data = {**VALID_MINIMAL, "jp_identifier": identifier}
    with pytest.raises(ValueError):
        Config.model_validate(data)


@pytest.mark.parametrize("identifier", ["Plex", "Noto", "Sarasa", "A", "SansSerifJP"])
def test_valid_jp_identifiers(identifier: str) -> None:
    data = {**VALID_MINIMAL, "jp_identifier": identifier}
    cfg = Config.model_validate(data)
    assert cfg.jp_identifier == identifier


def test_parse_codepoint_range() -> None:
    assert parse_codepoint_range("F179") == (0xF179, 0xF179)
    assert parse_codepoint_range("U+F179") == (0xF179, 0xF179)
    assert parse_codepoint_range("E000-E00A") == (0xE000, 0xE00A)


@pytest.mark.parametrize("key", ["", "XYZ", "F179-", "E00A-E000", "F179 F17A"])
def test_parse_codepoint_range_invalid(key: str) -> None:
    with pytest.raises(ValueError):
        parse_codepoint_range(key)


def test_nerd_font_glyph_scales() -> None:
    data = dict(VALID_MINIMAL)
    data["nerd_font_glyph_scales"] = {"F179": 1.15, "E000-E00A": 0.9}
    cfg = Config.model_validate(data)
    assert cfg.nerd_font_glyph_scales == {"F179": 1.15, "E000-E00A": 0.9}


def test_jp_stroke_width_defaults_to_zero() -> None:
    cfg = Config.model_validate(VALID_MINIMAL)
    assert cfg.jp_stroke_width == 0


def test_jp_stroke_width() -> None:
    data = dict(VALID_MINIMAL)
    data["jp_stroke_width"] = 8
    cfg = Config.model_validate(data)
    assert cfg.jp_stroke_width == 8


def test_invalid_jp_stroke_width() -> None:
    data = dict(VALID_MINIMAL)
    data["jp_stroke_width"] = -1
    with pytest.raises(ValueError):
        Config.model_validate(data)


@pytest.mark.parametrize(
    "scales",
    [{"XYZ": 1.15}, {"F179": 0}, {"F179": -1.0}],
)
def test_invalid_nerd_font_glyph_scales(scales: dict[str, float]) -> None:
    data = dict(VALID_MINIMAL)
    data["nerd_font_glyph_scales"] = scales
    with pytest.raises(ValueError):
        Config.model_validate(data)


def test_em_must_match_ascent_plus_descent() -> None:
    data = dict(VALID_MINIMAL)
    data["em"] = 9999
    with pytest.raises(ValueError):
        Config.model_validate(data)


def test_load_config_from_yaml(tmp_path: Path) -> None:
    import yaml

    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(VALID_MINIMAL), encoding="utf-8")
    cfg = load_config(p)
    assert cfg.jp_identifier == "Plex"


def test_plex_config_font_paths_exist() -> None:
    cfg = load_config(Path("config/plex.yaml"))
    paths = [
        cfg.fonts.en.regular,
        cfg.fonts.en.bold,
        cfg.fonts.jp.regular,
        cfg.fonts.jp.bold,
    ]
    for path in paths:
        assert path.exists(), f"{path} should exist"
