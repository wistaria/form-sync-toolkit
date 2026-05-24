# OAuth Setup

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
