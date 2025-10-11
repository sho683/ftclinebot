# LINE Bot - 足の健康管理アプリケーション

足の健康状態を判定し、適切な運動プログラムを週次で提供するLINE Botアプリケーション。
複数の企業・団体を同時にサポートするマルチテナント対応です。

---

## 🔄 最近の主要な更新（2025年10月）

### ✅ 12週間動画プログラム機能
- A/B評価用・C/D評価用それぞれ12本の動画を順番に配信
- 12週目の次は自動的に1週目に戻る（無限ループ）
- ユーザーごとに個別の週番号を管理

### ✅ 運動履歴の保存機能
- 新テーブル `exercise_history` を追加
- ユーザーの回答履歴を経時的に保存
- 統計分析・継続率の計算が可能

### ✅ 管理用API追加
- `/admin/history/all`: 全履歴表示
- `/admin/users/<bot_id>`: 全ユーザー一覧と統計
- `/history/<bot_id>`: 企業統計
- 読み取り専用で安全に使用可能

### ✅ クイックリプライ対応
- 運動回数の入力を選択式に変更（0回/1~3回/4~7回）
- ユーザーの操作が簡単に

### ✅ 個別スケジュール管理
- ユーザーごとに回答日から正確に7日後に送信
- 6時間ごとのチェックで日時のズレを防止

### ⚠️ 削除された機能
- D評価の医療機関受診推奨メッセージ（全評価共通に統一）
- デバッグ用スクリプト（`check_logs.py`, `check_users.py`）
- 未使用コード（`line_api.py`, `FootTip`テーブル）

---

## 主な機能

- 足の健康状態チェック (A/B/C/D評価)
- 評価に応じた運動プログラムの提供（YouTube動画）
- **12週間の動画プログラム**（A/B用・C/D用それぞれ12本、自動ループ）
- ユーザーごとの個別スケジュール管理
- 週次クイックリプライによる運動継続確認
- **運動履歴の自動保存**（経時的データの蓄積）
- 管理用ダッシュボードAPI（履歴確認、統計情報）
- 複数企業の同時運用サポート

## 技術スタック

- Python 3.9+
- Flask
- LINE Messaging API SDK v3
- SQLAlchemy (PostgreSQL)
- APScheduler（6時間ごとの個別リマインダー）

## アーキテクチャ

- **マルチテナント対応**: 1つのアプリで複数企業のLINE Botを運用
- **個別スケジュール**: ユーザーごとに回答日から7日後にリマインダー送信
- **週番号管理**: 各ユーザーが12週分の動画を順番に受け取る

---

## 本番環境へのデプロイ手順

### 前提条件

- LINE Developers アカウントとチャネルの作成（企業ごとに1チャネル）
- PostgreSQL データベース（Render.com推奨）
- ホスティングサービス（Render.com推奨）

---

### 1. 環境変数の設定

#### **必須の環境変数**

```bash
# データベース接続（Internal URLを推奨）
DATABASE_URL=postgresql://user:password@host:5432/database

# 企業B（稼働させる企業）の設定
COMPANY3_CHANNEL_SECRET=あなたのChannel Secret
COMPANY3_ACCESS_TOKEN=あなたのAccess Token
COMPANY3_NAME=企業B
```

#### **オプションの環境変数**

```bash
# 動画URL（A/B評価用 - 12週分）
EXERCISE_VIDEO_AB_WEEK1=https://www.youtube.com/watch?v=...
EXERCISE_VIDEO_AB_WEEK2=https://www.youtube.com/watch?v=...
...
EXERCISE_VIDEO_AB_WEEK12=https://www.youtube.com/watch?v=...

# 動画URL（C/D評価用 - 12週分）
EXERCISE_VIDEO_CD_WEEK1=https://www.youtube.com/watch?v=...
EXERCISE_VIDEO_CD_WEEK2=https://www.youtube.com/watch?v=...
...
EXERCISE_VIDEO_CD_WEEK12=https://www.youtube.com/watch?v=...

# サムネイル画像URL（オプション、設定しない場合はデフォルトURL）
EXERCISE_THUMBNAIL_AB_WEEK1=https://...
EXERCISE_THUMBNAIL_CD_WEEK1=https://...
```

#### **複数企業を運用する場合**

```bash
# 企業Aを追加
COMPANY1_CHANNEL_SECRET=...
COMPANY1_ACCESS_TOKEN=...
COMPANY1_NAME=企業A

# 企業Bを追加
COMPANY2_CHANNEL_SECRET=...
COMPANY2_ACCESS_TOKEN=...
COMPANY2_NAME=企業B
```

---

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

---

### 3. データベースのセットアップ

アプリケーション起動時に自動的にマイグレーションが実行されます。

**テーブル構成:**
- `companies`: 企業情報（bot_id, name）
- `users`: ユーザー情報（評価結果、週番号、企業ID）
- `message_logs`: メッセージ履歴

---

### 4. LINE Webhook URLの設定

LINE Developer Console → Messaging API設定 → Webhook URL:

```
https://あなたのドメイン.com/callback/company3
```

**重要**: `company3`の部分は環境変数の`COMPANY3_*`と対応します。

複数企業の場合：
- 企業A: `/callback/company1`
- 企業B: `/callback/company2`
- 企業C: `/callback/company3`

---

### 5. アプリケーションの起動

```bash
gunicorn main:app
```

または開発環境：

```bash
python main.py
```

---

## システムの動作フロー

### 初回登録（ユーザーがA〜Dを入力）
1. ユーザーが「A」を送信
2. Bot: 「足健診結果の入力ありがとうございます！1週間後に新しい運動メニューを配信します...」
3. データベースに`current_week = 0`を保存

### 1週間後（スケジューラーが自動実行）
4. Bot → ユーザー: クイックリプライで「この1週間で運動は何回できましたか？」
   - 選択肢: `0回` / `1~3回` / `4~7回`

### ユーザーが回答
5. ユーザーが「1~3回」をタップ
6. Bot: 励ましメッセージ + **1週目の動画**（Flex Message）
7. データベースに`current_week = 2`を保存

### 翌週以降
8. 毎週同じフローで、2週目→3週目→...→12週目の動画を順番に送信
9. 12週目の次は自動的に1週目に戻る（無限ループ）

---

## スケジューラーの仕組み

- **6時間ごと**にチェック（1日4回）
- 最後の回答から**正確に7日経過**したユーザーにのみ送信
- `question_sent`フラグで重複送信を防止
- ユーザーごとに個別のスケジュール

---

## コスト（LINE料金）

### 有料メッセージ
- 週1回のプッシュメッセージのみ（スケジューラーから）
- 返信メッセージは無料

### 月間コスト
- 1ユーザー = 月4通（週1通×4週）
- 50ユーザー = 月200通（フリープラン内）
- 375ユーザー = 月1,500通（ライトプラン: 5,000円）

---

## 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone [リポジトリURL]
cd Footlinebot-main

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定（.envファイルまたはターミナルで）
export DATABASE_URL="postgresql://..."
export COMPANY3_CHANNEL_SECRET="..."
export COMPANY3_ACCESS_TOKEN="..."

# 開発サーバーを起動
python main.py
```

### ローカルでのWebhookテスト

```bash
# ngrokで公開URL取得
ngrok http 10000

# 取得したURLをLINE Developer ConsoleのWebhook URLに設定
https://xxxx.ngrok.io/callback/company3
```

---

## データベース管理

### 既存データベースの確認

```bash
# psqlで接続
psql "postgresql://user:password@host/database"

# テーブル確認
\dt

# 企業一覧
SELECT id, bot_id, name FROM companies;

# ユーザー数確認
SELECT COUNT(*) FROM users;
```

### 新しいカラムの追加

`current_week`カラムは起動時に自動追加されます。
既存ユーザーには`default=0`が設定されます。

---

## データベース構造

### テーブル一覧

#### `companies`
企業情報を管理

#### `users`
ユーザー情報と現在の週番号を管理

#### `exercise_history` ⭐NEW
運動履歴を経時的に保存
- `user_id`: ユーザーID
- `response_date`: 回答日時
- `response_days`: 運動回数（0, 2, 5）
- `response_text`: 回答テキスト（"0回", "1~3回", "4~7回"）
- `week_number`: 送信した動画の週番号（1〜12）
- `foot_check_result`: 評価結果（A/B/C/D）
- `company_id`: 企業ID

ユーザーが回答するたびに自動的に履歴が保存されます。

#### `message_logs`
メッセージログ

---

## APIエンドポイント一覧

### ⚠️ 本番環境での注意事項

**以下のエンドポイントは実際にLINEメッセージを送信します！**
本番運用中は慎重に使用してください。

### 📱 メッセージ送信エンドポイント（要注意）

#### `/test/send-now` ⚠️ 危険
```bash
curl https://ftclinebot.onrender.com/test/send-now
```
- **即座に全ユーザーにメッセージを送信**
- テスト専用、本番では使用しないこと
- 誤送信に注意！

#### `/test/scheduler`
```bash
curl https://ftclinebot.onrender.com/test/scheduler
```
- 7日条件付きでメッセージ送信
- 該当するユーザーのみに送信
- 本番でも使用可能だが注意

---

### 📊 管理用エンドポイント（安全）

これらのエンドポイントは**読み取り専用**で、メッセージを送信しません。

#### `/health`
```bash
curl https://ftclinebot.onrender.com/health
```
ヘルスチェック

**レスポンス:**
```json
{
  "status": "ok",
  "companies": 1
}
```

#### `/history/<bot_id>`
```bash
curl https://ftclinebot.onrender.com/history/company3
```
企業全体の統計情報

**レスポンス:**
```json
{
  "company": "企業B",
  "total_users": 10,
  "total_responses": 45,
  "average_exercise_days": 3.2
}
```

#### `/history/<bot_id>?user_id=xxx`
```bash
curl "https://ftclinebot.onrender.com/history/company3?user_id=Uc8760f3a5b94ac1b7b931d2036da13f0"
```
特定ユーザーの運動履歴

**レスポンス:**
```json
{
  "user_id": "Uc8760f3a5b94ac1b7b931d2036da13f0",
  "username": "田中太郎",
  "foot_check_result": "A",
  "current_week": 3,
  "history": [
    {
      "date": "2025-10-11T10:30:00",
      "response_text": "1~3回",
      "response_days": 2,
      "week_number": 2
    }
  ]
}
```

#### `/admin/history/all` ⭐NEW
```bash
# デフォルト（最新100件）
curl https://ftclinebot.onrender.com/admin/history/all

# 件数を指定
curl https://ftclinebot.onrender.com/admin/history/all?limit=50
```
全ての運動履歴を取得（管理用）

**レスポンス:**
```json
{
  "total": 15,
  "limit": 100,
  "histories": [
    {
      "id": 15,
      "username": "田中太郎",
      "user_id": "Uc8760f3a5b94ac1b7b931d2036da13f0",
      "date": "2025-10-11T10:30:00",
      "response_text": "1~3回",
      "response_days": 2,
      "week_number": 2,
      "foot_check_result": "A"
    }
  ]
}
```

#### `/admin/users/<bot_id>` ⭐NEW
```bash
curl https://ftclinebot.onrender.com/admin/users/company3
```
全ユーザー一覧と統計情報

**レスポンス:**
```json
{
  "company": "企業B",
  "total_users": 5,
  "users": [
    {
      "user_id": "Uc8760f3a5b94ac1b7b931d2036da13f0",
      "username": "田中太郎",
      "foot_check_result": "A",
      "current_week": 3,
      "created_at": "2025-10-01T09:00:00",
      "total_responses": 5,
      "average_exercise_days": 3.4
    }
  ]
}
```

---

### 💡 エンドポイント使い分け

| 用途 | エンドポイント | 安全性 |
|-----|-------------|--------|
| ヘルスチェック | `/health` | ✅ 安全 |
| 企業統計 | `/history/<bot_id>` | ✅ 安全 |
| ユーザー履歴 | `/history/<bot_id>?user_id=xxx` | ✅ 安全 |
| 全履歴表示 | `/admin/history/all` | ✅ 安全 |
| 全ユーザー一覧 | `/admin/users/<bot_id>` | ✅ 安全 |
| テスト送信（条件なし） | `/test/send-now` | ⚠️ 危険（メッセージ送信） |
| テスト送信（7日条件） | `/test/scheduler` | ⚠️ 注意（メッセージ送信） |

---

### 🚨 本番運用前のチェックリスト

本番運用を開始する前に以下を確認してください：

- [ ] テスト用のユーザーアカウントで動作確認済み
- [ ] YouTube動画URLを全て設定済み（24本）
- [ ] Webhook URLが正しく設定されている（`/callback/company3`）
- [ ] データベースのバックアップ設定
- [ ] **`/test/send-now` を絶対に実行しない**（本番ユーザーに誤送信される）
- [ ] 環境変数が本番用に設定されている

### 🔒 本番運用中の注意点

- ⚠️ `/test/send-now` は**開発時のみ使用**、本番では絶対に実行しない
- ⚠️ `/test/scheduler` は緊急時のみ使用（通常は自動実行される）
- ✅ 管理用エンドポイント（`/admin/*`, `/history/*`, `/health`）は安全に使用可能

---

## 運動履歴データの活用

### SQLで直接確認

```sql
-- 全履歴
SELECT * FROM exercise_history ORDER BY response_date DESC;

-- ユーザーごとの統計
SELECT 
    u.username,
    COUNT(*) as total_responses,
    AVG(eh.response_days) as avg_days,
    MAX(eh.week_number) as max_week
FROM exercise_history eh
JOIN users u ON eh.user_id = u.id
GROUP BY u.id, u.username;

-- 週ごとの継続率
SELECT 
    week_number,
    COUNT(*) as responses,
    AVG(response_days) as avg_exercise_days
FROM exercise_history
GROUP BY week_number
ORDER BY week_number;
```

---

## トラブルシューティング

### Webhook接続エラー
- LINE Developer ConsoleでWebhook URLが正しいか確認
- `/callback/company3`のように`bot_id`が含まれているか確認
- SSL証明書が有効か確認（Renderなら自動）

### データベース接続エラー
- Internal URL（`dpg-xxxxx:5432`形式）を使用しているか確認
- External URLは遅く、帯域制限を消費するため非推奨

### スケジューラーが動作しない
- アプリケーションログで「Individual reminder scheduler started」を確認
- `program_sent_date`が正しく更新されているか確認
- `question_sent`フラグが正しくリセットされているか確認

### 動画が表示されない
- YouTube URLが正しいか確認
- サムネイル画像URLにアクセスできるか確認
- Flex Messageの形式が正しいか確認

### 週番号がリセットされない
- `current_week`が12の次に1に戻っているか確認
- ログで「週番号を12から1に更新しました」を確認

---

## セキュリティ

- 環境変数は必ず環境変数で管理（.envファイルは.gitignoreに追加）
- データベースURLは公開リポジトリにコミットしない
- Channel SecretとAccess Tokenは絶対に公開しない
- 本番環境ではDEBUGモードを無効化

---

## ライセンス

[ライセンス情報]

## サポート

問題が発生した場合は、Issuesページで報告してください。
