# Form Sync Toolkit

[English](README.md) | [日本語](README-ja.md)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Google Forms API](https://img.shields.io/badge/Google%20Forms-API-673AB7?logo=googleforms&logoColor=white)](https://developers.google.com/forms/api)
[![Google Drive API](https://img.shields.io/badge/Google%20Drive-API-4285F4?logo=googledrive&logoColor=white)](https://developers.google.com/drive)
[![Config](https://img.shields.io/badge/config-YAML-000000?logo=yaml&logoColor=white)](yaml-ja.md)
[![Author](https://img.shields.io/badge/author-Synge%20Todo-blue)](https://github.com/wistaria)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

YAML から Google フォームを作成・更新し、一覧表示、YAML への書き出し、差分確認もできる CLI ツールキットです。

## 機能

- YAML 定義から Google フォームを作成または更新
- 既存の Google フォームを YAML として書き出す
- Google フォームと YAML 定義を比較し、unified diff 形式で表示
- Google Drive 上の Google フォームをフルパス付きで一覧表示
- YAML の `path` に従って作成したフォームを Drive フォルダへ移動

## 要件

- Python 3.10+
- Google OAuth クライアント認証情報
- 初回実行時に Python の実行時依存関係をインストールするためのネットワーク接続

## セットアップ

スクリプトは初回実行時にシステムの一時ディレクトリへ仮想環境を作成し、`requirements.txt` から実行時依存関係を自動でインストールします。macOS では `/private/tmp/$UID/form-sync-toolkit` が使われます。

OAuth クライアント認証情報の取得手順は [oauth-ja.md](oauth-ja.md) を参照してください。初回の認証付きコマンド実行時に、ダウンロードした OAuth クライアント認証情報 JSON のパスを CLI で入力すると、`~/.config/form-sync-toolkit/credentials.json` にパーミッション `600` で保存されます。

認証情報やスコープを変更した場合は、保存済みの認証情報と `token.json` を削除してから再実行します。

```bash
rm -f ~/.config/form-sync-toolkit/credentials.json
rm -f token.json
```

初回認証時はブラウザが起動します。Google アカウントを選択してアクセスを許可し、自分で作成した OAuth アプリの未確認アプリ警告では、そのまま続行してください。

## 使い方

YAML からフォームを作成または更新:

```bash
python3 sync_form.py FORM.yaml
```

フォームを YAML に書き出し:

```bash
python3 export_form.py --form-id FORM_ID
```

出力先を指定して YAML に書き出し:

```bash
python3 export_form.py --form-id FORM_ID --output FORM.yaml
```

フォームと YAML を比較:

```bash
python3 check_form.py --form-id FORM_ID FORM.yaml
```

Google Drive 上のフォーム一覧を表示:

```bash
python3 list_form.py
```

YAML 形式の詳細は [yaml-ja.md](yaml-ja.md) を参照してください。

## スクリプトの挙動

- `sync_form.py`
  - `path` と `title` で既存フォームを検索
  - 0 件なら作成
  - 1 件なら更新
  - 2 件以上なら曖昧エラー
- `export_form.py`
  - Form ID から Google フォームを読み込み、正規化した YAML を出力
- `check_form.py`
  - 正規化した YAML と実際の Google フォームを比較
  - `title`、`description`、`path`、質問種別、選択肢、必須設定を確認
- `list_form.py`
  - フォーム名、ID、作成・更新日時、URL、Drive 上のフルパスを表示

## メモ

- `requirements.txt` にはスクリプトが自動インストールする実行時依存関係を置きます。
- `requirements-dev.txt` には `pytest` や `ruff` などの開発用ツールを置きます。
- `FORM_SYNC_TOOLKIT_NO_AUTO_VENV=1` を設定すると、自動仮想環境セットアップをスキップできます。
- OAuth クライアント認証情報は `~/.config/form-sync-toolkit/credentials.json` にパーミッション `600` で保存されます。
- OAuth トークンは実行時のカレントディレクトリに `token.json` として保存されます。

## 開発

ローカル開発では、自分で仮想環境を作成して、実行時依存関係と開発用依存関係の両方をインストールします。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.
