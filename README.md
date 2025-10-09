# LINE Bot - 足の健康管理アプリケーション

足の健康状態を判定し、適切な運動プログラムを週次で提供するLINE Botアプリケーション。
複数の企業・団体を同時にサポートするマルチテナント対応です。

## 主な機能

- 足の健康状態チェック (A/B/C/D評価)
- 評価に応じた運動プログラムの提供（YouTube動画）
- **12週間の動画プログラム**（A/B用・C/D用それぞれ12本、自動ループ）
- ユーザーごとの個別スケジュール管理
- 週次クイックリプライによる運動継続確認
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
