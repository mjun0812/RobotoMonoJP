"""CLI entrypoint. typer で `generate` / `print` を提供する."""

from __future__ import annotations

from pathlib import Path

import typer

from . import __version__

app = typer.Typer(add_completion=False, no_args_is_help=True)


StyleOption = typer.Option(
    None,
    "--style",
    help="生成対象style. 複数指定可 (未指定なら4種すべて).",
)


def _resolve_styles(styles: list[str] | None) -> list[str]:
    from .properties import STYLES

    if not styles:
        return list(STYLES)
    for s in styles:
        if s not in STYLES:
            raise typer.BadParameter(f"--style must be one of {STYLES}: got {s!r}")
    return styles


@app.command()
def generate(
    config: Path = typer.Option(..., "-c", "--config", exists=True, dir_okay=False, readable=True),
    output: Path = typer.Option(Path("dist"), "-o", "--output"),
    style: list[str] | None = StyleOption,
    no_nerd_font: bool = typer.Option(False, "--no-nerd-font", help="Nerd Font パッチをスキップ."),
    version_suffix: str = typer.Option(
        "", "--version-suffix", help="フォントversionに付与するsuffix."
    ),
) -> None:
    """config.yaml から8ファイル (4 style × ttf/otf) を生成する."""
    from .config import load_config
    from .generator import BuildRequest, build

    cfg = load_config(config)
    styles = _resolve_styles(style)
    version = f"{__version__}{version_suffix}"

    for style_name in styles:
        typer.echo(f"[generate] style={style_name}")
        request = BuildRequest(
            config=cfg,
            style=style_name,
            version=version,
            output_dir=output,
            apply_nerd_font=not no_nerd_font,
        )
        path = build(request)
        typer.echo(f"  -> {path}")


@app.command("print")
def print_command(
    font_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    sample: str = typer.Argument("", help="レンダリングする文字列."),
    output: Path = typer.Option(..., "-o", "--output"),
    size: int | None = typer.Option(None, "--size", help="レンダリングpt."),
) -> None:
    """指定フォントで文字列をPDFにレンダリングする."""
    from .printer import print_pdf

    result = print_pdf(font_path, sample, output, size=size)
    typer.echo(f"wrote {result}")


@app.command()
def eyecatch(
    font_path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output: Path = typer.Option(Path("eyecatch.svg"), "-o", "--output"),
    title: str | None = typer.Option(
        None, "--title", help="タイトル。未指定ならフォントのfamily名."
    ),
) -> None:
    """指定フォントでterminal風のアイキャッチSVGを生成する."""
    from .eyecatch import generate_eyecatch

    result = generate_eyecatch(font_path, output, title=title)
    typer.echo(f"wrote {result}")


def main() -> None:
    """`robotomonojp` entrypoint (project.scripts から呼ばれる)."""
    app()


if __name__ == "__main__":
    main()
