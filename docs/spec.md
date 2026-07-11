# Specification

RobotoMono、日本語Font、Nerd Fontを合成したフォントを生成する。

## 生成フォント

1つのconfigから1つのfamilyを生成する。

- RobotoMono由来の `WIDTH=1299` を維持。
- 半角=1299、全角=1849 (1.42:1)。
- 日本語の見た目重視、緩めの等幅。

`Regular` / `Bold` / `Italic` / `BoldItalic` の4スタイルを持つ。
合計で 4 style × (ttf, otf) = 8ファイル。

## 命名規則

JP Fontを差し替え可能にするため、`familyname` は `jp_identifier` から機械的に組み立てる。

- `RobotoMono{jp_identifier}`

例:

| jp_identifier | familyname         |
| ------------- | ------------------ |
| `Plex`        | `RobotoMonoPlex`   |
| `Noto`        | `RobotoMonoNoto`   |
| `Sarasa`      | `RobotoMonoSarasa` |

`jp_identifier` は `config.yaml` トップレベルに必須フィールドとして持ち、以下のバリデーションを課す。

- PascalCase (先頭大文字、以降 `[A-Za-z0-9]`)。
- ASCII英数字のみ。
- 1〜16文字。
- `"Mono"` との完全一致は禁止 (予約)。

`config.yaml` の `familyname` を明示指定すると上記ルールを上書きできる。

旧 `RobotoMonoJP` / `RobotoMonoJP-Mono` からはリネームとなる (breaking change、major bump)。

## Installation

FontForgeのPython bindingsが必要なため、Dockerで実行環境を用意する。

Base imageは `ubuntu:24.04` を使い、`apt` で `python3` (3.12) と `fontforge` を入れる。
`fontforge` bindingsは system python (`/usr/bin/python3`) に対して入るため、Docker内でも system python をそのまま使う。
`uv` を image に同梱し、`uv sync --system` で system python に依存を入れる。

`pyproject.toml` の `requires-python` は `>=3.12` とする。

Nerd Fontsリポジトリはサイズが27GB規模のため、`git submodule` + sparse-checkoutで `font-patcher` および `src/glyphs/` 配下のみを取得する。

DockerとリポジトリのマウントはMakefileで抽象化する。
`pyproject.toml` の `project.scripts` は Python entry point (`robotomonojp = "robotomonojp.cli:main"`) のみを登録し、Docker越しの呼び出しはMakefile targetから行う。

## CLI

### generate

Font作成endpoint。1回の呼び出しで8ファイルを一括生成する。

```bash
python -m robotomonojp generate -c config.yaml
python -m robotomonojp generate -c config.yaml -o dist/ --style Regular
```

CLIフラグ (基本):

- `-c` / `--config PATH` (必須): config.yamlへのpath。
- `-o` / `--output DIR`: 出力先ディレクトリ。デフォルト `dist/`。
- `--style STYLE`: 生成対象style。複数指定可。デフォルト4種すべて。

CLIフラグ (拡張):

- `--no-nerd-font`: Nerd Fontパッチを適用しない (デバッグ用)。
- `--version-suffix TEXT`: フォントversionにsuffixを付与する (dev buildで使用)。

`config.yaml` とCLIで同じ項目が指定された場合はCLIが上書きする。
フォントパスや詳細なメトリクスは `config.yaml` にのみ記述する。

### print

Font確認用のPDFを出力する。

```bash
python -m robotomonojp print <font-path> "string" --output <output path>
```

`<font-path>` はttf/otfファイルへの直接pathを受け取る。
指定文字列を 24pt でレンダリングしてA4にまとめる。サイズは `--size` オプションで変更可能。
FontForge の複数サイズ出力 (waterfall) は空のPDFを出力するバグがあるため、単一サイズとしている。

### eyecatch

terminal風のアイキャッチSVGを出力する。

```bash
python -m robotomonojp eyecatch <font-path> -o <output path> [--title TEXT]
```

指定フォントのglyph outlineを fontTools でSVG pathに変換して埋め込むため、閲覧環境にフォントが無くても指定フォントの字形で表示される。タイトル未指定時はフォントのfamily名を使う。fontforge非依存のためDocker外でも実行できる。

## config.yaml

トップレベルにメタデータとメトリクスをフラットに持つ。

```yaml
jp_identifier: Plex # 必須。命名規則の識別子。

metadata: # 任意。未指定ならハードコードのデフォルト値
  copyright: "..."
  vendor: "mjun"

fonts: # 必須
  en:
    regular: path/to/RobotoMono-Regular.ttf
    bold: path/to/RobotoMono-Bold.ttf
  jp:
    regular: path/to/JP-Regular.ttf
    bold: path/to/JP-Bold.ttf

italic_angle: -11 # 任意 (デフォルト -11)

# familyname 未指定なら `RobotoMono{jp_identifier}` = "RobotoMonoPlex"
ascent: 1638
descent: 410
em: 2048
en_width: 1299
jp_width: 1849
jp_scale_offset: 0.10
jp_stroke_width: 0 # 任意。JP glyphをmerge前に太らせるFontForge stroke幅
underline_pos: -200
underline_height: 100
os2_ascent: 2146
os2_descent: 555

nerd_font_glyph_scales: # 任意。Nerd Font patch後のglyph補正 (codepoint/レンジ → 倍率)
  "F179": 1.15
```

パーサは pydantic v2 でバリデーションする。

## Font生成パイプライン

1. EN読み込み: RobotoMonoを開き、encoding以外は変更しない (旧 `main.py` と同じ)。
2. JPスケール適用: 旧 `main.py` と同じく `ascent / 元JPフォントのascent + jp_scale_offset` 倍に拡縮し、半角カナ幅を `en_width`、全角幅を `jp_width` に合わせる。かな・漢字以外の記号は合成元フォントの送り幅を基準に、全角EMに近ければ `jp_width`、半角EMに近ければ `en_width` に合わせる。
3. JP stroke補正: `jp_stroke_width` が0より大きい場合、JP fontだけをmerge前に FontForge の `stroke` で太らせる。advance widthはstroke前の値に戻す。
4. Merge: 新規空フォントに EN → JP の順で `mergeFonts` する (同名glyphはEN側を優先)。
5. Italic生成: `Italic` / `BoldItalic` の場合は Regular / Bold から `italic_angle` で skew する (EN/JPとも)。
6. リガチャ削除: 最終フォントから `liga` / `dlig` / `clig` / `hlig` / `calt` feature を持つglyphと `U+FB00-FB4F` を削除する。
7. Nerd Font patch: submodule内の `font-patcher` を subprocessで呼び出し、`--complete` を適用する。patch後、`nerd_font_glyph_scales` で指定されたglyphをadvanceを変えずにink中心基準で拡大縮小する (公式patcherが小さく埋め込むappleロゴなどの補正)。

## Metadata

- `familyname`: 命名規則 (`RobotoMono{jp_identifier}`) から自動生成する。`config.yaml` の `familyname` で明示指定して上書き可能。
- `copyright`: デフォルトはハードコード、`config.yaml` で上書き可能。
- `version`: `pyproject.toml` の `project.version` を単一のsource of truthとし、SFNT versionに埋め込む。

## Output

出力先は `dist/{familyname}/{familyname}-{style}.(ttf|otf)` で固定。
`--output` フラグでルートディレクトリを変更可能。

## CI

GitHub Actionsで並列jobを走らせる。

- `lint`: `ruff format --check` と `ruff check` を実行する。
- `test`: `pytest` を実行する。対象は以下のPure Python部分に限る。
  - `config.yaml` の pydantic バリデーション。
  - Helper関数 (skew angle計算、幅推定など FontForge非依存の計算)。
  - typer `CliRunner` によるCLI引数パーサイング。
- `docker`: `docker build` の成否確認。

## CD

`v*` タグpushをトリガーにrelease jobを走らせる。

1. jobの先頭で `pyproject.toml` の version と tag名 (先頭 `v` を除いたもの) の一致を確認する。不一致ならfail-fastする。
2. Docker imageをbuildする。
3. `config/*.yaml` の全configに対して `generate` を実行し、`dist/` を成果物として取り出す。
4. `gh release create` で全config分のfont (config数 × 4 style × (ttf, otf)) をindividual assetとしてuploadする。

フォントversionは `pyproject.toml` のversionと同期する。

## Dependencies

- CLI: `typer`
- Config validation: `pydantic` v2
- YAML: `PyYAML`
- Font生成: `fontforge` (apt), `psMat` (fontforge同梱)
- アイキャッチ生成: `fonttools`

## Reference

- <https://github.com/ryanoasis/nerd-fonts#font-patcher>
- <https://github.com/fontforge/fontforge/blob/master/INSTALL.md>
- <https://fonts.google.com/specimen/Roboto+Mono>
