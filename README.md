# Form Sync Toolkit

[![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Google Forms API](https://img.shields.io/badge/Google%20Forms-API-673AB7?logo=googleforms&logoColor=white)](https://developers.google.com/forms/api)
[![Google Drive API](https://img.shields.io/badge/Google%20Drive-API-4285F4?logo=googledrive&logoColor=white)](https://developers.google.com/drive)
[![YAML](https://img.shields.io/badge/Config-YAML-000000?logo=yaml&logoColor=white)](yaml.md)
[![Author](https://img.shields.io/badge/Author-Synge%20Todo-blue)](https://github.com/wistaria)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

YAML から Google フォームを作成・更新、一覧表示、YAML 書き出しする CLI ツール

## 準備

### 仮想環境

- 仮想環境を作成して有効化する

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 認証情報の設定

- OAuth クライアント ID の取得手順は [oauth.md](oauth.md) を参照

- 環境変数 `GOOGLE_CREDENTIALS_JSON` を設定する

```bash
export GOOGLE_CREDENTIALS_JSON={"installed":{"client_id": ... ["http://localhost"]}}
```

- 認証情報を変更した場合は、`token.json` を削除する

```bash
rm -f token.json
```

## 実行

- YAML を作成または更新: `python3 sync_form.py FORM.yaml`
- Form ID から YAML を生成: `python3 export_form.py --form-id <FORM_ID>`
- Form ID と YAML を比較: `python3 check_form.py --form-id <FORM_ID> FORM.yaml`
- Google Drive 上のフォーム一覧を表示: `python3 list_form.py`

- YAML 形式の詳細は [yaml.md](yaml.md) を参照

- 初回実行時、または `token.json` 削除後はブラウザが起動する
  - Google アカウントを選択してアクセスを許可する
  - 同意画面の「このアプリは Google で確認されていません」は無視して続行する

## スクリプトの挙動

- `sync_form.py`
  - `path` + `title` で既存フォームを検索
  - 0 件なら作成、1 件なら更新、2 件以上なら曖昧エラー
- `list_form.py`
  - フォーム名と Drive 上のフルパスを表示
- `export_form.py`
  - Form ID から YAML を生成
- `check_form.py`
  - Form ID の Google フォームと YAML を比較
  - 質問数、タイトル、種類、オプションの差分を確認

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for the full text.
