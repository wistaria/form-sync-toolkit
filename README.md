# Google Form Generator

## 準備: 認証情報 OAuth Client ID の取得

1. Google Cloud プロジェクト作成
   1. Google Cloud Console
   2. プロジェクト選択
   3. 「新しいプロジェクト」
   4. 任意の名前 (例: google-forms-cli)

2. Google Forms API と Google Drive API を有効化
   1. API とサービス > ライブラリ
   2. Google Forms API と Google Drive API を有効にする

3. OAuth 同意画面設定
   1. API とサービス > OAuth 同意画面
   2. ブランディング
   3. 開始
   4. 入力例：
      - アプリ名: Google Forms CLI
      - ユーザサポートメール: 自分の Gmail
      - 対象: 外部
      - 連絡先情報: 自分の Gmail

4. Test Users 追加
   1. API とサービス > OAuth 同意画面
   2. ブランディング
   3. 対象
   4. Test users > Add users
   5. 自分の Gmail を追加

5. OAuth Client ID 作成
   1. API とサービス > 認証情報
   2. 認証情報を作成 > OAuth Client ID
   3. 入力例：
      - クライアントの種類: デスクトップアプリ
      - 名前: Google Forms CLI
   4. JSONをダウンロード
   5. 保存

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
