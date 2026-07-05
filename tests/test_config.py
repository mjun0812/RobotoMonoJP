"""config.yaml パーサのバリデーションテスト."""

from __future__ import annotations

from pathlib import Path

import pytest

from robotomonojp.config import Config, load_config

VALID_MINIMAL: dict = {
    "jp_identifier": "Plex",
    "fonts": {
        "en": {"regular": "en-r.ttf", "bold": "en-b.ttf"},
        "jp": {"regular": "jp-r.ttf", "bold": "jp-b.ttf"},
    },
    "variants": {
        "mono": {
            "ascent": 1638,
            "descent": 410,
            "em": 2048,
            "en_width": 1024,
            "jp_width": 2048,
            "jp_scale": 0.9,
            "underline_pos": -200,
            "underline_height": 100,
            "os2_ascent": 1638,
            "os2_descent": 410,
        }
    },
}


def test_valid_minimal_config() -> None:
    cfg = Config.model_validate(VALID_MINIMAL)
    assert cfg.jp_identifier == "Plex"
    assert cfg.familyname_for("mono") == "RobotoMonoPlex-Mono"


def test_familyname_defaults_by_variant() -> None:
    data = dict(VALID_MINIMAL)
    data["variants"] = {
        "proportional": {**VALID_MINIMAL["variants"]["mono"], "en_width": 1299, "jp_width": 1849},
        "mono": VALID_MINIMAL["variants"]["mono"],
    }
    cfg = Config.model_validate(data)
    assert cfg.familyname_for("proportional") == "RobotoMonoPlex"
    assert cfg.familyname_for("mono") == "RobotoMonoPlex-Mono"


def test_familyname_override() -> None:
    data = dict(VALID_MINIMAL)
    data["variants"] = {"mono": {**VALID_MINIMAL["variants"]["mono"], "familyname": "MyMono"}}
    cfg = Config.model_validate(data)
    assert cfg.familyname_for("mono") == "MyMono"


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


def test_em_must_match_ascent_plus_descent() -> None:
    data = dict(VALID_MINIMAL)
    variant = {**VALID_MINIMAL["variants"]["mono"], "em": 9999}
    data["variants"] = {"mono": variant}
    with pytest.raises(ValueError):
        Config.model_validate(data)


def test_at_least_one_variant_required() -> None:
    data = dict(VALID_MINIMAL)
    data["variants"] = {}
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
