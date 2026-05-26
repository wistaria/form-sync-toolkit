# YAML 形式マニュアル

[English](yaml.md) | [日本語](yaml-ja.md)

`sync_form.py` で使用する YAML 形式を定義します

## 概要

- `path` + `title` で既存フォームを検索
- 1 件なら更新、0 件なら新規作成
- `path` 指定時はフォルダを自動作成

## トップレベル項目

```yaml
title: フォームタイトル
documentTitle: Drive上のドキュメント名（任意）
description: フォーム説明（任意）
path: /Forms/業務アンケート（任意）
questions:
  - title: 質問1
    type: short
```

- `title`:
  - 必須
  - フォームタイトル
  - 検索キーとして使用
- `documentTitle`:
  - 任意
  - 新規作成時のみ反映
  - 更新時は変更されない
- `description`:
  - 任意
  - フォーム説明
- `path`:
  - 任意
  - Google Drive 上の配置先フォルダパス
  - 省略時は Drive ルート
- `questions`:
  - 任意（省略時は質問なし）
  - 質問オブジェクトの配列

## 質問オブジェクト

各質問は以下の形式です。

```yaml
- title: 質問文
  type: short | paragraph | radio | checkbox | dropdown
  required: true | false   # 任意（省略時 false）
  description: 補足説明      # 任意
  options:                 # radio/checkbox/dropdown で必須
    - 選択肢A
    - 選択肢B
  shuffle: true | false    # radio/checkbox のみ有効
```

### type ごとの要件

- `short`
  - 1行テキスト
  - `options` は不要
- `paragraph`
  - 複数行テキスト
  - `options` は不要
- `radio`
  - ラジオボタン
  - `options` 必須
  - `shuffle` 任意
- `checkbox`
  - チェックボックス
  - `options` 必須
  - `shuffle` 任意
- `dropdown`
  - ドロップダウン
  - `options` 必須
  - `shuffle` は無視される

## 更新時の挙動

既存フォームが見つかった場合は次を実行します。

1. タイトルと説明を更新
2. 既存の質問を全削除
3. YAML の `questions` で再作成
4. `path` 指定があればフォームをそのフォルダに移動

## フォーム特定ルール

- 検索条件: `path` 配下で `title` が一致
- 0 件: 新規作成
- 1 件: 更新
- 2 件以上: 曖昧エラー

## エラーになりやすいケース

- `title` がない
- `type` が未対応（`short/paragraph/radio/checkbox/dropdown` 以外）
- `radio/checkbox/dropdown` で `options` がない
- 同じ `path` に同名フォームが複数ある

## 注意事項

- フォルダパス内に同名フォルダが複数ある場合は曖昧エラー

## 完全サンプル

```yaml
title: アンケート
documentTitle: 2026Q2 業務改善アンケート
description: 今後の業務改善の参考にするためのアンケートです
path: /Forms/業務アンケート

questions:
  - title: 年齢を教えてください
    type: radio
    required: true
    options:
      - 20歳未満
      - 20-30歳
      - 31-40歳
      - 41-50歳
      - 51歳以上
    shuffle: true

  - title: 業務で使用しているツールは何ですか？（複数選択可）
    type: checkbox
    required: true
    options:
      - Excel
      - Google Sheets
      - Slack
      - Microsoft Teams
      - その他

  - title: 最もよく使うツールはどれですか？
    type: dropdown
    options:
      - Excel
      - Google Sheets
      - Slack

  - title: ご意見があればご記入ください
    type: paragraph
    required: false
    description: 自由記述で入力してください
```
