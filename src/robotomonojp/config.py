"""config.yaml のスキーマ定義とバリデーション."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

JP_IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]{0,15}$")


class MetadataConfig(BaseModel):
    """フォントに埋め込むメタデータ."""

    model_config = ConfigDict(extra="forbid")

    copyright: str | None = None
    vendor: str | None = None


class WeightPaths(BaseModel):
    """Regular / Bold のペアパス."""

    model_config = ConfigDict(extra="forbid")

    regular: Path
    bold: Path


class FontsConfig(BaseModel):
    """EN / JP それぞれの入力フォントパス."""

    model_config = ConfigDict(extra="forbid")

    en: WeightPaths
    jp: WeightPaths


class VariantConfig(BaseModel):
    """1つのvariant (mono / proportional) のメトリクスとfamilyname."""

    model_config = ConfigDict(extra="forbid")

    familyname: str | None = None
    ascent: int
    descent: int
    em: int
    en_width: int
    jp_width: int
    jp_scale: float
    underline_pos: int
    underline_height: int
    os2_ascent: int
    os2_descent: int

    @model_validator(mode="after")
    def _check_em(self) -> VariantConfig:
        if self.ascent + self.descent != self.em:
            msg = f"ascent + descent ({self.ascent + self.descent}) must equal em ({self.em})"
            raise ValueError(msg)
        return self


class VariantsConfig(BaseModel):
    """proportional / mono の両方 (両方任意、少なくとも片方必須)."""

    model_config = ConfigDict(extra="forbid")

    proportional: VariantConfig | None = None
    mono: VariantConfig | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> VariantsConfig:
        if self.proportional is None and self.mono is None:
            raise ValueError("variants must contain at least one of 'proportional' or 'mono'")
        return self


class Config(BaseModel):
    """config.yaml のトップレベルスキーマ."""

    model_config = ConfigDict(extra="forbid")

    jp_identifier: str = Field(..., description="RobotoMono{jp_identifier} のPascalCase識別子")
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    fonts: FontsConfig
    italic_angle: float = -11.0
    variants: VariantsConfig

    @field_validator("jp_identifier")
    @classmethod
    def _check_identifier(cls, value: str) -> str:
        if value == "Mono":
            raise ValueError('jp_identifier must not be "Mono" (conflicts with variant suffix)')
        if not JP_IDENTIFIER_PATTERN.match(value):
            raise ValueError(
                f"jp_identifier must be PascalCase ASCII alphanumeric, 1-16 chars: got {value!r}"
            )
        return value

    def familyname_for(self, variant: str) -> str:
        """variant名 ('proportional'/'mono') から familyname を組み立てる."""
        cfg = getattr(self.variants, variant)
        if cfg is None:
            raise ValueError(f"variant {variant!r} is not configured")
        if cfg.familyname is not None:
            return cfg.familyname
        base = f"RobotoMono{self.jp_identifier}"
        return f"{base}-Mono" if variant == "mono" else base


def load_config(path: Path) -> Config:
    """config.yaml を読み、Configインスタンスを返す."""
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"config root must be a mapping, got {type(data).__name__}")
    return Config.model_validate(data)
