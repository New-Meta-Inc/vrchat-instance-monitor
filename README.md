# VRChat Instance Monitor

VRChatの特定ワールドのアクティブインスタンス数と各インスタンスのユーザー数を定期的に監視・記録するPythonスクリプトです。

## 機能

このスクリプトは以下の情報を10分ごとに取得してテキストファイルに記録します。

- アクティブインスタンス数
- 各インスタンスのユーザー数
- 各インスタンスのタイプ（public, friends+, friends, invite+, invite, hidden）
- 各インスタンスの収容人数と満員状態
- プラットフォーム別のユーザー数（Windows, Android, iOS）
- ワールド全体の総ユーザー数

## 必要な環境

- Python 3.11以上
- requestsライブラリ
- python-dotenvライブラリ（.envファイルの自動読み込み用）

## インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/NewMetaInc/vrchat-instance-monitor.git
cd vrchat-instance-monitor
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`ファイルを`.env`にコピーして、VRChatの認証情報を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集して以下の情報を入力してください。

```bash
# VRChatの認証情報
VRCHAT_USERNAME=your_username_or_email
VRCHAT_PASSWORD=your_password

# 監視するワールドID（デフォルト値が設定されています）
VRCHAT_WORLD_ID=wrld_7bb60bf6-3c69-4039-a5d6-0cbbda092290

# 出力ファイル名（オプション）
OUTPUT_FILE=vrchat_instances.txt

# データ収集間隔（分単位、デフォルト: 10）
INTERVAL_MINUTES=10
```

## 使用方法

### 基本的な使用方法

`.env`ファイルを設定した後、以下のコマンドでスクリプトを実行します。

**重要**: スクリプトは起動時に同じディレクトリの`.env`ファイルを自動的に読み込みます。

```bash
python vrchat_instance_monitor.py
```

### 環境変数を直接指定して実行

```bash
export VRCHAT_USERNAME="your_username"
export VRCHAT_PASSWORD="your_password"
export VRCHAT_WORLD_ID="wrld_7bb60bf6-3c69-4039-a5d6-0cbbda092290"
python vrchat_instance_monitor.py
```

### バックグラウンドで実行

```bash
nohup python vrchat_instance_monitor.py > monitor.log 2>&1 &
```

### 停止方法

フォアグラウンドで実行している場合は`Ctrl+C`で停止できます。

バックグラウンドで実行している場合は以下のコマンドでプロセスを停止します。

```bash
ps aux | grep vrchat_instance_monitor.py
kill <PID>
```

## 出力形式

データは指定したテキストファイル（デフォルト: `vrchat_instances.txt`）に以下の形式で記録されます。

```
================================================================================
収集日時: 2025-11-20T12:00:00.123456
ワールド名: Example World
ワールドID: wrld_7bb60bf6-3c69-4039-a5d6-0cbbda092290
総ユーザー数: 47
パブリックユーザー数: 46
プライベートユーザー数: 1
アクティブインスタンス数: 5
--------------------------------------------------------------------------------

インスタンス #1
  ID: 12345~public
  ユーザー数: 10
  タイプ: public
  最大収容人数: 16
  満員: いいえ
  プラットフォーム別: {'standalonewindows': 8, 'android': 2}

インスタンス #2
  ID: 67890~friends
  ユーザー数: 8
  タイプ: friends
  最大収容人数: 16
  満員: いいえ
  プラットフォーム別: {'standalonewindows': 7, 'android': 1}

...
================================================================================
```

## ログファイル

実行ログは`vrchat_monitor.log`ファイルに記録されます。エラーやデバッグ情報を確認する際に参照してください。

## 注意事項

### VRChat APIについて

VRChat APIは**非公式**であり、VRChatによって公式にサポートされていません。以下の点に注意してください。

- APIは予告なく変更される可能性があります
- 過度なリクエストはアカウント停止の原因となる可能性があります
- [VRChat Creator Guidelines](https://hello.vrchat.com/creator-guidelines)を遵守してください

### セッション管理

VRChat APIはセッション数に制限があります。このスクリプトは認証情報（cookie）を自動的に保存・再利用することで、セッション数を最小限に抑えています。

### レート制限

APIのレート制限を考慮して、各インスタンスの詳細情報取得の間に0.5秒の待機時間を設けています。

### セキュリティ

- `.env`ファイルや認証情報を含むファイルは**絶対にGitリポジトリにコミットしないでください**
- `.gitignore`に`.env`と`vrchat_auth_cookie.txt`が含まれていることを確認してください

## トラブルシューティング

### 認証エラーが発生する

- VRChatのユーザー名（またはメールアドレス）とパスワードが正しいか確認してください
- 2段階認証が有効な場合は、一時的に無効にするか、別の認証方法を検討してください

### データが取得できない

- ワールドIDが正しいか確認してください
- VRChat APIが一時的にダウンしている可能性があります
- ログファイル（`vrchat_monitor.log`）を確認してエラーメッセージを確認してください

### インスタンス情報が不完全

- 一部のインスタンス（プライベートやhidden）は詳細情報を取得できない場合があります
- これは正常な動作です

## ライセンス

MIT License

## 免責事項

このスクリプトはVRChatの非公式APIを使用しています。使用は自己責任で行ってください。このスクリプトの使用によって生じたいかなる損害についても、開発者は責任を負いません。

## 貢献

バグ報告や機能リクエストは、GitHubのIssuesページでお願いします。プルリクエストも歓迎します。

## 参考資料

- [VRChat.community API Documentation](https://vrchat.community/)
- [VRChat Creator Guidelines](https://hello.vrchat.com/creator-guidelines)
