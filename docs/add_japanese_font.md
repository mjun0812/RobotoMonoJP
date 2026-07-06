# 日本語フォントの追加ガイド

新しい日本語フォントを合成対象に追加するときの手順、調整すべき設定、確認すべき文字をまとめる。

## 手順

1. 日本語フォントの `Regular` と `Bold` を用意する。
   - `Italic` と `BoldItalic` は CLI が `Regular` / `Bold` から生成するため不要。
   - 形式は TTF を推奨する (既存フォントと同じ)。
2. ライセンスを確認する。
   - 生成物を配布する場合は、元フォントのライセンス表記と再配布条件を確認する。
   - ライセンスファイルをフォントと同じディレクトリに同梱する。
3. フォントファイルをリポジトリ内に配置する。
   - 例: `fonts/NotoSansJP/NotoSansJP-Regular.ttf`
   - 例: `fonts/NotoSansJP/NotoSansJP-Bold.ttf`
4. `config/*.yaml` を追加する。
   - 既存の `config/plex.yaml` をコピーして、`jp_identifier` と `fonts.jp` を変更する。
5. メトリクスを調整する (後述)。
6. 生成して確認する (後述)。

設定例:

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
ascent: 1638
descent: 410
em: 2048
en_width: 1299
jp_width: 1849
jp_scale_offset: 0.10
underline_pos: -200
underline_height: 100
os2_ascent: 2146
os2_descent: 555
```

`jp_identifier` は family name (`RobotoMono{jp_identifier}`) に使われる。

- 先頭大文字の ASCII 英数字、最大16文字。
- `Mono` は予約されているため使えない。
- 例: `jp_identifier: Noto` → `RobotoMonoNoto`

全設定キーの一覧は [README の設定ファイル](../README.md#設定ファイル) を参照。

## 調整すべき設定

日本語フォントごとにメトリクスが異なるため、以下のキーはフォントを差し替えるたびに見直す。

| キー                                 | 調整の観点                                                                                                                                                                                                   |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `jp_scale_offset`                    | 日本語 glyph のスケールは `ascent / 元JPフォントのascent + jp_scale_offset` で決まる。元フォントの ascent が違うと同じ offset でも見た目サイズが変わるため、英字と並べたときの大きさのバランスを見て調整する |
| `jp_width`                           | 全角文字の advance width。`en_width` との比がそのまま半角:全角の見た目比になる (デフォルトは 1299:1849 ≈ 1:1.42)                                                                                             |
| `os2_ascent` / `os2_descent`         | 行の高さ (hhea / OS/2 win)。日本語 glyph は ascent/descent を超えて ink を持つことがあり、値が小さいと Terminal で上下が欠ける。スケール調整後に最も背の高い文字が収まるか確認する                           |
| `ascent` / `descent` / `em`          | 基本は `1638 / 410 / 2048` のまま変えない。`ascent + descent == em` の制約がある                                                                                                                             |
| `underline_pos` / `underline_height` | 下線の位置と太さ。通常はデフォルトのままでよい                                                                                                                                                               |

## 幅の自動処理と気をつける文字

生成パイプラインは日本語フォント側の glyph 幅を次のルールで正規化する
(`src/robotomonojp/generator.py` の `_load_jp_font()` / `_normalize_symbol_width()`)。

| 対象                                             | 処理                                                                                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| 半角カナ (U+FF61-FF9E)                           | `en_width` に設定                                                                                                              |
| ひらがな・カタカナ・CJK漢字                      | `jp_width` に設定                                                                                                              |
| 上記以外で East Asian Width が W/F (全角) の文字 | `jp_width` に設定                                                                                                              |
| 上記以外 (曖昧幅 A・中立 N を含む)               | Terminal が1セルで扱うため `en_width` に収める。ink がセル幅の 92% (`SYMBOL_INK_RATIO`) を超える場合は縮小し、セル中央に寄せる |
| zero-width glyph (結合文字)                      | 幅を変更しない                                                                                                                 |

Roboto Mono が同じ文字を持つ場合は merge で EN 側が優先されるため、日本語フォント側の glyph は使われない。

フォントを追加したら、次のカテゴリの文字を実際に表示して確認する。

| カテゴリ            | 確認する文字の例              | 見るポイント                                                                                   |
| ------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------- |
| 全角かな・漢字      | `あ 漢 日 が ぱ`              | 大きさのバランス (`jp_scale_offset`)、濁点・半濁点の潰れ                                       |
| 半角カナ            | `ｱ ﾎﾟ ｶﾞ`                     | `en_width` に収まっているか、濁点の判別                                                        |
| 曖昧幅記号          | `○ ● ■ ★ → ※`                 | Terminal (WezTerm / VSCode Terminal) で `echo "○○ →→ ★★"` して隣と重ならないか、小さすぎないか |
| 全角英数・全角記号  | `Ａ １ 。 、 「」 （） ￥`    | `jp_width` になっているか (EAW = W/F 判定)                                                     |
| 罫線・Nerd Font記号 | `─ │ ┌ ` + Powerline記号      | Nerd Fonts patcher 由来なので日本語フォントには依存しないが、表示崩れがないか                  |
| 行の高さ            | `｜零瞬麗鬱髙` など背の高い字 | Terminal で上下が欠けないか (`os2_ascent` / `os2_descent`)                                     |

補足:

- 画数の多い漢字 (`漢` など) は ink が advance を数%超えることがある。隣の全角文字と僅かに重なって見えるが、元フォント由来の挙動で許容している。
- リガチャは生成の最終段階で削除される。縦書き feature は維持される。

## 検証方法

```bash
# Regular だけ生成 (Docker)
make generate-regular CONFIG=config/{font}.yaml

# サンプル文字列をPDFで確認 (TEXT省略時は全文字種を網羅したデフォルトを使用)
make print FONT=dist/{familyname}/{familyname}-Regular.ttf

# glyph幅の実測 (fontforge)
docker run --rm -v "$PWD:/app" -w /app robotomonojp:dev python3 -c "
import fontforge
font = fontforge.open('dist/{familyname}/{familyname}-Regular.ttf')
for ch in 'Aあ漢ｱ○→★Ａ':
    g = font[ord(ch)]
    xmin, _, xmax, _ = g.boundingBox()
    print(f'{ch}: width={g.width} ink=({xmin:.0f},{xmax:.0f})')
"

# インストール (dist内の全familyについて既存を置き換え。macOS/Linux対応)
make reinstall OUTPUT=dist
```

Terminal での最終確認は、フォントをインストールした上で WezTerm / VSCode Terminal のフォント設定を切り替えて行う。

最後に `make lint` と `make test` を実行し、README の生成例や配布対象を変える必要がある場合は該当箇所を更新する。
