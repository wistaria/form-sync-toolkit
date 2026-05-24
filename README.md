# Form Sync Toolkit

[![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Google Forms API](https://img.shields.io/badge/Google%20Forms-API-673AB7?logo=googleforms&logoColor=white)](https://developers.google.com/forms/api)
[![Google Drive API](https://img.shields.io/badge/Google%20Drive-API-4285F4?logo=googledrive&logoColor=white)](https://developers.google.com/drive)
[![YAML](https://img.shields.io/badge/Config-YAML-000000?logo=yaml&logoColor=white)](yaml.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

YAML から Google Forms を作成・更新、一覧表示や YAML 書き出しもできる CLI ツール

作者: 藤堂眞治 / Synge Todo

## 準備: 認証情報の設定

- OAuth Client ID 取得手順は [oauth.md](oauth.md) を参照

- 環境変数 GOOGLE_CREDENTIALS_JSON の設定

```bash
export GOOGLE_CREDENTIALS_JSON={"installed":{"client_id": ... ["http://localhost"]}}
```

- 認証情報を更新した場合、認証情報を切り替える場合は、アクセストークン token.json を削除する

```bash
rm -f token.json
```

## 実行

- YAML を作成または更新: `python3 sync_form.py FORM.yaml`
- Form ID から YAML を生成: `python3 export_form.py --form-id <FORM_ID>`
- Form ID と YAML を比較: `python3 check_form.py --form-id <FORM_ID> FORM.yaml`
- Google Drive 上のフォーム一覧を表示: `python3 list_form.py`

- YAML 形式の詳細は [yaml.md](yaml.md) を参照

- 初回実行時(あるいは、アクセストークン token.json を削除した直後)には、ブラウザが立ち上がる
- Google アカウントを選択し、アクセスを許可する
- 同意画面で「このアプリは Google で確認されていません」という警告が出るが問題ない。続行をクリックして進む

## スクリプトの挙動

- `sync_form.py`
  - YAML の `path` + `title` で既存フォームを検索
  - 見つからなければ作成、見つかれば更新する upsert スクリプト
  - フォルダパス内に同名フォルダが複数ある場合、曖昧エラーになります
- `list_form.py`
  - フォーム名とあわせて Drive 上のフルパスを表示
- `export_form.py`
  - 指定した Form ID から YAML を生成する
- `check_form.py`
  - 指定した Form ID の Google Forms と YAML を比較する
  - 質問数、タイトル、種類、オプションなどの差分を確認する

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for the full text.
