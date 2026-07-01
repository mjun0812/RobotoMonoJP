"""CLI entrypoint. typer で `generate` / `print` を提供する."""

from __future__ import annotations

from pathlib import Path

import typer

from . import __version__

app = typer.Typer(add_completion=False, no_args_is_help=True)


VariantOption = typer.Option(
    "all",
    "--variant",
    help="生成対象variant. proportional / mono / all のいずれか.",
    show_default=True,
)
StyleOption = typer.Option(
    None,
    "--style",
    help="生成対象style. 複数指定可 (未指定なら4種すべて).",
)


def _resolve_variants(variant: str) -> list[str]:
    if variant == "all":
        return ["proportional", "mono"]
    if variant in {"proportional", "mono"}:
        return [variant]
    raise typer.BadParameter(f"--variant must be one of proportional|mono|all: got {variant!r}")


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
    variant: str = VariantOption,
    style: list[str] | None = StyleOption,
    no_nerd_font: bool = typer.Option(False, "--no-nerd-font", help="Nerd Font パッチをスキップ."),
    version_suffix: str = typer.Option(
        "", "--version-suffix", help="フォントversionに付与するsuffix."
    ),
) -> None:
    """config.yaml から16ファイル (2 variant × 4 style × ttf/otf) を生成する."""
    from .config import load_config
    from .generator import BuildRequest, build

    cfg = load_config(config)
    variants = _resolve_variants(variant)
    styles = _resolve_styles(style)
    version = f"{__version__}{version_suffix}"

    for variant_name in variants:
        if getattr(cfg.variants, variant_name) is None:
            typer.echo(f"[skip] variant={variant_name} is not configured")
            continue
        for style_name in styles:
            typer.echo(f"[generate] variant={variant_name} style={style_name}")
            request = BuildRequest(
                config=cfg,
                variant_name=variant_name,
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
    size: list[int] | None = typer.Option(None, "--size", help="レンダリングpt (複数指定可)."),
) -> None:
    """指定フォントで文字列を複数サイズのPDFにレンダリングする."""
    from .printer import DEFAULT_SIZES, print_pdf

    sizes = tuple(size) if size else DEFAULT_SIZES
    result = print_pdf(font_path, sample, output, sizes=sizes)
    typer.echo(f"wrote {result}")


def main() -> None:
    """`robotomonojp` entrypoint (project.scripts から呼ばれる)."""
    app()


if __name__ == "__main__":
    main()
