# Roboto Mono JP

![Preview](docs/images/font_preview.png)

Roboto Mono と日本語フォントを合成し、Nerd Fonts の glyph を追加したプログラミング用フォントを生成する CLI です。

Download: <https://github.com/mjun0812/RobotoMonoJP/releases>

## 生成されるフォント

`config.yaml` の `jp_identifier` から family name を決定します。

例として `jp_identifier: Plex` の場合、以下の2 variantを生成します。

- `RobotoMonoPlex`
  - Roboto Mono 由来の幅を維持する proportional variant
- `RobotoMonoPlex-Mono`
  - 半角幅 1024、全角幅 2048 の mono variant

各 variant には `Regular` / `Bold` / `Italic` / `BoldItalic` があり、各 style で `ttf` と `otf` を出力します。
全 variant を生成すると 16 ファイルになります。

出力先は次の形式です。

```text
dist/{familyname}/{familyname}-{style}.ttf
dist/{familyname}/{familyname}-{style}.otf
```

## 必要なもの

- Docker
- Git submodule

FontForge の Python bindings が必要なため、フォント生成は Docker 上で実行します。

## セットアップ

```bash
git clone https://github.com/mjun0812/RobotoMonoJP.git
cd RobotoMonoJP
make submodule-init
make docker-build
```

`make submodule-init` は `vendor/nerd-fonts` を初期化し、Nerd Fonts の `font-patcher` と必要な glyph だけを sparse-checkout します。

## 生成

`config/plex.yaml` を使って全 variant / 全 style を生成します。

```bash
make generate
```

Regular だけを生成する場合は次のコマンドを使います。

```bash
make generate-regular
```

Makefile を使わずに直接実行する場合は、Docker コンテナ内で CLI を呼び出します。

```bash
docker run --rm -v "$PWD:/app" -w /app robotomonojp:dev \
  python3 -m robotomonojp generate -c config/plex.yaml -o dist
```

主な CLI オプションは次の通りです。

```bash
python3 -m robotomonojp generate \
  --config config/plex.yaml \
  --output dist \
  --variant all \
  --style Regular
```

- `-c` / `--config`: 設定ファイル
- `-o` / `--output`: 出力先ディレクトリ。デフォルトは `dist`
- `--variant`: `proportional` / `mono` / `all`
- `--style`: `Regular` / `Bold` / `Italic` / `BoldItalic`。複数指定可
- `--no-nerd-font`: Nerd Fonts の patch をスキップ
- `--version-suffix`: フォント version に suffix を付与

## フォント確認PDF

生成済みフォントでサンプル文字列を PDF に出力できます。

```bash
make print FONT=dist/RobotoMonoPlex/RobotoMonoPlex-Regular.ttf TEXT="Roboto Mono 日本語 123" OUT=preview.pdf
```

直接実行する場合は次の形式です。

```bash
python3 -m robotomonojp print <font-path> "sample text" --output preview.pdf
```

## 日本語フォントを追加する手順

1. 日本語フォントの `Regular` と `Bold` を用意します。
   - `Italic` と `BoldItalic` は CLI が `Regular` / `Bold` から生成します。
2. ライセンスを確認します。
   - 生成物を配布する場合は、元フォントのライセンス表記と再配布条件を確認してください。
3. フォントファイルをリポジトリ内に配置します。
   - 例: `fonts/NotoSansJP/NotoSansJP-Regular.ttf`
   - 例: `fonts/NotoSansJP/NotoSansJP-Bold.ttf`
4. `config/*.yaml` を追加します。
   - 既存の `config/plex.yaml` をコピーして、`jp_identifier` と `fonts.jp` を変更します。
5. 必要に応じて `variants` のメトリクスを調整します。
   - `ascent + descent` は `em` と一致している必要があります。
6. Docker 上で生成して確認します。

設定例です。

```yaml
jp_identifier: Noto

metadata:
  vendor: mjun

fonts:
  en:
    regular: fonts/RobotoMono/RobotoMono-Regular.ttf
    bold: fonts/RobotoMono/RobotoMono-Bold.ttf
  jp:
    regular: fonts/NotoSansJP/NotoSansJP-Regular.ttf
    bold: fonts/NotoSansJP/NotoSansJP-Bold.ttf

italic_angle: -11

variants:
  proportional:
    ascent: 1638
    descent: 410
    em: 2048
    en_width: 1299
    jp_width: 1849
    jp_scale: 1.10
    underline_pos: -200
    underline_height: 100
    os2_ascent: 2146
    os2_descent: 555

  mono:
    ascent: 1638
    descent: 410
    em: 2048
    en_width: 1024
    jp_width: 2048
    jp_scale: 0.9
    underline_pos: -200
    underline_height: 100
    os2_ascent: 1638
    os2_descent: 410
```

`jp_identifier` は family name に使われます。

- 先頭大文字の ASCII 英数字にしてください。
- 最大16文字です。
- `Mono` は variant suffix と衝突するため使えません。

`jp_identifier: Noto` の場合、出力 family name は `RobotoMonoNoto` と `RobotoMonoNoto-Mono` になります。

## 設定ファイル

設定ファイルのトップレベルは次の構成です。

- `jp_identifier`: family name に使う識別子
- `metadata`: フォントに埋め込む任意のメタデータ
- `fonts.en`: Roboto Mono の `regular` / `bold`
- `fonts.jp`: 日本語フォントの `regular` / `bold`
- `italic_angle`: italic 生成時の傾き
- `variants.proportional`: proportional variant のメトリクス
- `variants.mono`: mono variant のメトリクス

詳細な仕様は [docs/spec.md](docs/spec.md) を参照してください。

## 開発

```bash
make lint
make test
```

`make lint` は `ruff format --check` と `ruff check` を実行します。
`make test` は `pytest` を実行します。

## 参考

- [SF Mono を使って最高のプログラミング用フォントを作った話 - Qiita](https://qiita.com/delphinus/items/f472eb04ff91daf44274)
- [ryanoasis/nerd-fonts](https://github.com/ryanoasis/nerd-fonts)
- [IBM/plex](https://github.com/IBM/plex)
- [Google Fonts](https://fonts.google.com/specimen/Roboto+Mono)
- [RobotoMonoに日本語を合成したフォントを作りました](https://note.mjunya.com/posts/2021-12-28-roboto-mono-jp/)
- [プログラミング用フォント Utatane](https://github.com/nv-h/Utatane/blob/master/utatane.py)
- [プログラミング用合成フォント PleckJP を作った](https://ryota2357.com/blog/2023/dev-font-pleckjp/)
- [プログラミング用合成フォント PleckJP の合成スクリプトの実装解説](https://ryota2357.com/blog/2023/pleck-jp-impl-exp/)
- [ryota2357/PleckJP](https://github.com/ryota2357/PleckJP)
