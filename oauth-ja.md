# 認証情報 OAuth Client ID の取得

[English](oauth.md) | [日本語](oauth-ja.md)

1. Google Cloud プロジェクト作成
   - Google Cloud Console を開く
   - プロジェクト選択
     - 「新しいプロジェクト」
     - 任意の名前 (例: google-forms-cli)

2. Google Forms API と Google Drive API を有効化
   - API とサービス > ライブラリ
   - Google Forms API と Google Drive API を有効にする

3. OAuth 同意画面設定
   - API とサービス > OAuth 同意画面
   - ブランディング > 開始
   - 入力例:
     - アプリ名: Form Sync Toolkit
     - ユーザサポートメール: 自分の Gmail
     - 対象: 外部
     - 連絡先情報: 自分の Gmail

4. Test users を追加
   - API とサービス > OAuth 同意画面
   - ブランディング > 対象
   - Test users > Add users
   - 自分の Gmail を追加

5. OAuth Client ID 作成
   - API とサービス > 認証情報
   - 認証情報を作成 > OAuth Client ID
   - 入力例:
     - クライアントの種類: デスクトップアプリ
     - 名前: Form Sync Toolkit
   - JSON をダウンロードして保存する
   - 初回の認証付き CLI 実行時に、その JSON ファイルのパスを入力する。toolkit が `~/.config/form-sync-toolkit/credentials.json` へ mode `600` でコピーして保存する
