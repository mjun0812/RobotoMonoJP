# AGENTS.md

## 基本方針

- 常に日本語で応答する。
- 変更は依頼された範囲に限定し、隣接コードの不要な整形やリファクタは行わない。
- `vendor/nerd-fonts` はサブモジュール由来の外部コードとして扱い、明示依頼がない限り編集しない。
- 生成物の `dist/`、一時作業用の `tmp/`、フォント確認用の出力ファイルは、依頼や検証に必要な場合だけ変更する。

## プロジェクト概要

- Python 3.12 以上の CLI プロジェクト。
- パッケージ本体は `src/robotomonojp/` にある。
- テストは `tests/` にある。
- フォント family ごとの設定は `config/*.yaml` にある。
- 仕様や追加手順は `docs/` にある。
- FontForge Python bindings が必要なフォント生成処理は Docker 経由で実行する。

## 開発コマンド

- 依存関係の実行は `uv` を使う。
- テスト: `make test`
- lint: `make lint`
- format: `make format`
- typecheck: `make typecheck`
- Docker image build: `make docker-build`
- Nerd Fonts submodule 初期化: `make submodule-init`
- 全フォント生成: `make generate`
- 特定設定だけ生成: `make generate CONFIG=config/{font}.yaml`
- Regular だけ生成: `make generate-regular`

## Python コーディング規約

- 型ヒントを必ず書く。
- `Any` は既存の FontForge binding 境界など、具体型を置けない箇所に限定する。
- 関数・クラスには Google スタイルの docstring を書く。
- 文字列への変数埋め込みは f-string を使う。
- 既存の module 分割と命名に合わせる。
- CLI 変更時は `src/robotomonojp/cli.py`、設定変更時は `src/robotomonojp/config.py` と関連テストを確認する。

## 検証方針

- バグ修正では、可能な限り先に再現テストを追加してから修正する。
- 設定バリデーションの変更は `tests/test_config.py` にテストを追加する。
- フォント合成ロジックの変更は、軽量な単体テストで検証できる範囲を優先する。
- FontForge や Docker が必要な生成確認は、必要最小限の `CONFIG` や `--style Regular` で行う。
- 変更後は原則として `make test` を実行し、Python コードを触った場合は `make lint` も実行する。

## Markdown

- Markdown を編集した場合は `oxfmt` で整形する。
- README や docs を更新するときは、実際の Makefile や CLI の挙動と一致させる。

## Git

- ユーザーの未コミット変更を戻さない。
- コミットを作成する場合は Conventional Commits 形式にする。
- コミットメッセージの 2 行目は空行にし、3 行目以降で何をなぜ変更したかを具体的に書く。
