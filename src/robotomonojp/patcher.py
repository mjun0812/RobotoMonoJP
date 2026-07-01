"""Nerd Fonts の font-patcher を subprocess で呼び出す薄いラッパー."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# submoduleのrootパス. リポジトリ直下 vendor/nerd-fonts.
DEFAULT_NERD_FONTS_ROOT = Path("vendor/nerd-fonts")


class NerdFontPatcherError(RuntimeError):
    """font-patcher 実行失敗時に投げる."""


def find_font_patcher(root: Path = DEFAULT_NERD_FONTS_ROOT) -> Path:
    """submodule 内の font-patcher スクリプトのパスを返す."""
    candidate = root / "font-patcher"
    if not candidate.exists():
        msg = (
            f"Nerd Fonts の font-patcher が {candidate} に見つかりません. "
            "submodule を初期化しましたか?"
        )
        raise NerdFontPatcherError(msg)
    return candidate


def patch(
    input_font: Path,
    output_dir: Path,
    *,
    nerd_fonts_root: Path = DEFAULT_NERD_FONTS_ROOT,
    complete: bool = True,
    mono: bool = False,
    extra_args: list[str] | None = None,
) -> Path:
    """入力フォントに Nerd Fonts パッチを当て、outputディレクトリのttfパスを返す."""
    if shutil.which("fontforge") is None:
        raise NerdFontPatcherError(
            "fontforge コマンドが見つかりません. Docker外で実行していませんか?"
        )

    script = find_font_patcher(nerd_fonts_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        "fontforge",
        "-script",
        str(script),
        str(input_font),
        "--outputdir",
        str(output_dir),
    ]
    if complete:
        cmd.append("--complete")
    if mono:
        cmd.append("--mono")
    if extra_args:
        cmd.extend(extra_args)

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise NerdFontPatcherError(
            f"font-patcher failed (exit {proc.returncode})\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    generated = sorted(output_dir.glob("*.ttf"))
    if not generated:
        raise NerdFontPatcherError(f"font-patcher が {output_dir} にttfを生成しませんでした")
    return generated[-1]
