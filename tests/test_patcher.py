"""patcher module のテスト. subprocess 呼び出し部分."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from robotomonojp import patcher


def test_font_patcher_preserves_source_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_font = tmp_path / "Input.ttf"
    input_font.write_bytes(b"font")
    nerd_fonts_root = tmp_path / "nerd-fonts"
    nerd_fonts_root.mkdir()
    (nerd_fonts_root / "font-patcher").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    def fake_which(command: str) -> str | None:
        return "/usr/bin/fontforge" if command == "fontforge" else None

    def fake_run(
        cmd: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert "--makegroups" in cmd
        assert cmd[cmd.index("--makegroups") + 1] == "-1"
        output_dir = Path(cmd[cmd.index("--outputdir") + 1])
        (output_dir / "Input.ttf").write_bytes(b"patched")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(patcher.shutil, "which", fake_which)
    monkeypatch.setattr(patcher.subprocess, "run", fake_run)

    result = patcher.patch(input_font, tmp_path / "out", nerd_fonts_root=nerd_fonts_root)

    assert result.name == "Input.ttf"
