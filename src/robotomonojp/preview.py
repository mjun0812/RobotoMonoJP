"""静的HTMLフォントプレビューの生成."""

from __future__ import annotations

import os
from html import escape
from pathlib import Path
from typing import cast
from urllib.parse import quote

FONT_FACE_NAME = "RobotoMonoJPPreview"

SAMPLES: list[tuple[str, list[str]]] = [
    (
        "英数字",
        [
            "Il1| 0O8B $@& {}[]() <> -> => === !==",
            "abcdefghijklmnopqrstuvwxyz",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789",
        ],
    ),
    (
        "日本語",
        [
            "あいうえお がぎぐげご ぱぴぷぺぽ",
            "アイウエオ ヴァヴィヴヴェヴォ",
            "漢字日本語 鬱 曜 齋 纏",
            "ｱｲｳｴｵ ｶﾞｷﾞｸﾞｹﾞｺﾞ ﾊﾟﾋﾟﾌﾟﾍﾟﾎﾟ",
        ],
    ),
    (
        "混在",
        [
            'const message = "Roboto Mono 日本語 123";',
            "Git branch: feature/日本語-font-balance",
            "ABC日本語abc123 あAアｱ 0OIl1",
        ],
    ),
    (
        "空白",
        [
            "半角: A B C D",
            "全角: A　B　C　D",
            "混在: A B　C D　E",
        ],
    ),
    (
        "記号",
        [
            "。、，．・「」『』（）［］｛｝",
            "○●□■◇◆△▲▽▼→←↑↓※±×÷",
            "Powerline:     ",
        ],
    ),
]


def _font_format(font_path: Path) -> str:
    """拡張子からCSSのfont formatを返す."""
    suffix = font_path.suffix.lower()
    if suffix == ".otf":
        return "opentype"
    if suffix == ".woff":
        return "woff"
    if suffix == ".woff2":
        return "woff2"
    return "truetype"


def _font_url(font_path: Path, output: Path) -> str:
    """HTMLから見たフォントファイルの相対URLを返す."""
    output_dir = output.parent.resolve()
    rel_path = os.path.relpath(font_path.resolve(), output_dir)
    return quote(Path(rel_path).as_posix(), safe="/:")


def _family_name(font_path: Path) -> str:
    """フォントのfamily名を返す."""
    from fontTools.ttLib import TTFont

    font = TTFont(str(font_path))
    try:
        name = cast(str | None, font["name"].getBestFamilyName())
        return name or font_path.stem
    finally:
        font.close()


def _sample_block(title: str, lines: list[str]) -> str:
    """サンプル表示ブロックのHTMLを返す."""
    rows = "\n".join(f'        <p class="sample-line">{escape(line)}</p>' for line in lines)
    return f"""      <section class="sample-block">
        <h2>{escape(title)}</h2>
{rows}
      </section>"""


def generate_preview(font_path: Path, output: Path, title: str | None = None) -> Path:
    """指定フォントを確認する静的HTMLを生成する.

    Args:
        font_path: 表示確認に使うttf/otf/woff/woff2のpath.
        output: 出力先HTMLのpath.
        title: ページタイトル. 未指定ならフォントのfamily名.
    """
    font_path = font_path.resolve()
    output = output.resolve()
    page_title = title or _family_name(font_path)
    font_url = _font_url(font_path, output)
    font_format = _font_format(font_path)
    sample_blocks = "\n".join(_sample_block(section, lines) for section, lines in SAMPLES)
    sizes = "\n".join(
        f'        <div class="size-row" style="font-size: {size}px">'
        f"<span>{size}px</span><p>ABC日本語abc123 あAアｱ 0OIl1</p></div>"
        for size in (11, 12, 13, 14, 16, 20, 24)
    )

    html = f"""<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(page_title)} preview</title>
    <style>
      @font-face {{
        font-family: "{FONT_FACE_NAME}";
        src: url("{font_url}") format("{font_format}");
        font-display: block;
      }}

      :root {{
        color-scheme: light dark;
        --bg: #f6f7f9;
        --panel: #ffffff;
        --text: #20242a;
        --muted: #667085;
        --border: #d5d9e0;
        --grid: rgba(34, 40, 49, 0.14);
        --dark-bg: #1f2329;
        --dark-panel: #282d35;
        --dark-text: #eef1f5;
        --dark-muted: #a8b0bd;
        --dark-border: #3e4652;
        --dark-grid: rgba(238, 241, 245, 0.18);
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        line-height: 1.5;
      }}

      main {{
        max-width: 1160px;
        margin: 0 auto;
        padding: 32px 20px 48px;
      }}

      header {{
        margin-bottom: 24px;
      }}

      h1 {{
        margin: 0 0 6px;
        font-size: 28px;
        line-height: 1.2;
      }}

      h2 {{
        margin: 0 0 12px;
        font-size: 15px;
        color: var(--muted);
      }}

      .meta {{
        margin: 0;
        color: var(--muted);
        font-size: 13px;
        overflow-wrap: anywhere;
      }}

      .preview-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
      }}

      .sample-block,
      .size-block {{
        border: 1px solid var(--border);
        border-radius: 8px;
        background: var(--panel);
        padding: 16px;
      }}

      .font-sample {{
        font-family: "{FONT_FACE_NAME}", monospace;
        font-feature-settings: "kern" 0;
      }}

      .sample-line {{
        margin: 8px 0 0;
        min-height: 28px;
        padding: 4px 8px;
        border-radius: 4px;
        background-image: repeating-linear-gradient(
          to right,
          transparent 0,
          transparent calc(1ch - 1px),
          var(--grid) calc(1ch - 1px),
          var(--grid) 1ch
        );
        font-family: "{FONT_FACE_NAME}", monospace;
        font-feature-settings: "kern" 0;
        font-size: 20px;
        line-height: 1.55;
        white-space: pre;
        overflow-x: auto;
      }}

      .size-block {{
        margin-top: 16px;
      }}

      .size-row {{
        display: grid;
        grid-template-columns: 56px minmax(0, 1fr);
        gap: 12px;
        align-items: baseline;
        margin-top: 10px;
        font-family: "{FONT_FACE_NAME}", monospace;
        font-feature-settings: "kern" 0;
      }}

      .size-row span {{
        color: var(--muted);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 12px;
      }}

      .size-row p {{
        margin: 0;
        white-space: pre;
        overflow-x: auto;
      }}

      .theme-dark {{
        margin-top: 16px;
        background: var(--dark-bg);
        color: var(--dark-text);
        border-radius: 8px;
        padding: 16px;
      }}

      .theme-dark h2 {{
        color: var(--dark-muted);
      }}

      .theme-dark .sample-line {{
        background-color: var(--dark-panel);
        background-image: repeating-linear-gradient(
          to right,
          transparent 0,
          transparent calc(1ch - 1px),
          var(--dark-grid) calc(1ch - 1px),
          var(--dark-grid) 1ch
        );
        border: 1px solid var(--dark-border);
      }}

      @media (max-width: 520px) {{
        main {{
          padding: 24px 12px 36px;
        }}

        .preview-grid {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <h1>{escape(page_title)}</h1>
        <p class="meta">{escape(str(font_path))}</p>
      </header>
      <div class="preview-grid font-sample">
{sample_blocks}
      </div>
      <section class="size-block">
        <h2>サイズ別</h2>
{sizes}
      </section>
      <section class="theme-dark">
        <h2>ダーク背景</h2>
        <p class="sample-line">const message = "Roboto Mono 日本語 123";</p>
        <p class="sample-line">半角: A B C D / 全角: A　B　C　D</p>
      </section>
    </main>
  </body>
</html>
"""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output
