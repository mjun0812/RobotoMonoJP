"""config.yaml のスキーマ定義とバリデーション."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

JP_IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]{0,15}$")
CODEPOINT_RANGE_PATTERN = re.compile(
    r"^(?:U\+)?([0-9A-Fa-f]{1,6})(?:-(?:U\+)?([0-9A-Fa-f]{1,6}))?$"
)


def parse_codepoint_range(key: str) -> tuple[int, int]:
    """'F179' や 'E000-E00A' 形式のキーを (start, end) のcodepointに変換する."""
    matched = CODEPOINT_RANGE_PATTERN.match(key)
    if matched is None:
        raise ValueError(f"invalid codepoint range: {key!r} (expected 'F179' or 'E000-E00A')")
    start = int(matched.group(1), 16)
    end = int(matched.group(2), 16) if matched.group(2) else start
    if start > end:
        raise ValueError(f"invalid codepoint range: {key!r} (start > end)")
    return start, end


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


class Config(BaseModel):
    """config.yaml のトップレベルスキーマ."""

    model_config = ConfigDict(extra="forbid")

    jp_identifier: str = Field(..., description="RobotoMono{jp_identifier} のPascalCase識別子")
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    fonts: FontsConfig

    italic_angle: float = -11.0
    familyname: str | None = None
    ascent: int
    descent: int
    em: int
    en_width: int
    jp_width: int
    jp_scale_offset: float = Field(
        ..., description="JPスケール (ascent / 元JPフォントのascent) に加算するoffset"
    )
    jp_stroke_width: int = Field(
        default=0,
        ge=0,
        description="JP glyphをmerge前に太らせるFontForge stroke幅。0なら補正しない",
    )
    underline_pos: int
    underline_height: int
    os2_ascent: int
    os2_descent: int
    nerd_font_glyph_scales: dict[str, float] = Field(
        default_factory=dict,
        description="Nerd Font patch後に拡大縮小するglyph. キーは 'F179' か 'E000-E00A' 形式",
    )

    @field_validator("nerd_font_glyph_scales")
    @classmethod
    def _check_glyph_scales(cls, value: dict[str, float]) -> dict[str, float]:
        for key, factor in value.items():
            parse_codepoint_range(key)
            if factor <= 0:
                raise ValueError(f"scale for {key!r} must be positive: got {factor}")
        return value

    @field_validator("jp_identifier")
    @classmethod
    def _check_identifier(cls, value: str) -> str:
        if value == "Mono":
            raise ValueError('jp_identifier must not be "Mono" (reserved)')
        if not JP_IDENTIFIER_PATTERN.match(value):
            raise ValueError(
                f"jp_identifier must be PascalCase ASCII alphanumeric, 1-16 chars: got {value!r}"
            )
        return value

    def familyname_for(self, mono: bool = False) -> str:
        """familynameを返す. mono版では末尾に-Monoを付ける."""
        familyname = self.familyname or f"RobotoMono{self.jp_identifier}"
        return f"{familyname}-Mono" if mono else familyname

    @model_validator(mode="after")
    def _check_em(self) -> Config:
        if self.ascent + self.descent != self.em:
            msg = f"ascent + descent ({self.ascent + self.descent}) must equal em ({self.em})"
            raise ValueError(msg)
        return self


def load_config(path: Path) -> Config:
    """config.yaml を読み、Configインスタンスを返す."""
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"config root must be a mapping, got {type(data).__name__}")
    return Config.model_validate(data)
