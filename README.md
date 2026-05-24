# Google Form Generator

- OAuth Client ID 取得手順は [oauth.md](oauth.md) を参照

## 準備: 認証情報の設定

1. 環境変数 GOOGLE_CREDENTIALS_JSON の設定

```bash
export GOOGLE_CREDENTIALS_JSON={"installed":{"client_id": ... ["http://localhost"]}}
```

1. 注: 認証情報を更新した場合、認証情報を切り替える場合は、アクセストークン token.json を削除する

```bash
rm -f token.json
```

## 実行

- YAML 形式の詳細は [yaml.md](yaml.md) を参照

1. 初回実行時(あるいは、アクセストークン token.json を削除した直後)には、ブラウザが立ち上がる
2. Google アカウントを選択し、アクセスを許可する
3. 注: 同意画面で「このアプリは Google で確認されていません」という警告が出るが問題ない。続行をクリックして進む

## YAML 設定

- `path`: フォームを配置する Google Drive 上のフォルダパス
  - 例: `/Forms/業務アンケート`
  - 省略時は Drive ルートに配置される
  - 指定したフォルダが存在しない場合は自動作成される

## スクリプトの挙動

- `sync_form.py`
  - YAML の `path` + `title` で既存フォームを検索
  - 見つからなければ作成、見つかれば更新
  - 実行後、YAML の `path` が指定されていればそのフォルダに移動
- `list_form.py`
  - フォーム名とあわせて Drive 上のフルパスを表示
