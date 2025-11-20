# インスタンス数0問題の修正内容

## 問題の概要

インスタンスが実際に存在しているにもかかわらず、スクリプトがインスタンス数を0として記録してしまう問題が発生していました。

## 原因分析

以下の可能性が考えられます。

1. **APIレスポンスのエラーを見逃していた**: HTTPステータスコードが200でもエラーレスポンスの可能性
2. **データ構造の検証不足**: インスタンスリストの型や構造を検証していなかった
3. **ログ情報の不足**: 問題の原因を特定するための詳細なログが不足していた

## 実装した修正内容

### 1. レスポンス検証の強化

**修正前**:
```python
world_info = self.api.get_world_info(self.world_id)
if not world_info:
    logger.error("ワールド情報の取得に失敗しました")
    return None

instances = world_info.get('instances', [])
```

**修正後**:
```python
world_info = self.api.get_world_info(self.world_id)
if not world_info:
    logger.error("ワールド情報の取得に失敗しました")
    return None

# レスポンスの型検証
if not isinstance(world_info, dict):
    logger.error(f"ワールド情報が辞書型ではありません: type={type(world_info)}")
    return None

instances = world_info.get('instances', [])

# インスタンスリストの型検証
if not isinstance(instances, list):
    logger.error(f"インスタンスリストがリスト型ではありません: type={type(instances)}")
    logger.error(f"instances値: {instances}")
    instances = []
```

### 2. 詳細なログ出力の追加

**API取得時のログ**:
```python
logger.debug(f"ワールド情報取得レスポンス: status={response.status_code}")
logger.debug(f"ワールド情報取得成功: name={data.get('name')}, occupants={data.get('occupants')}, instances_count={len(data.get('instances', []))}")
logger.debug(f"インスタンスデータのサンプル: {instances[:3]}")
```

**データ収集時のログ**:
```python
logger.info(f"ワールド情報: name={world_info.get('name')}, occupants={world_info.get('occupants')}")
logger.info(f"取得したインスタンス数: {len(instances)}")
logger.info(f"インスタンス #{idx + 1}: ID={instance_id}, ユーザー数={user_count}")
```

### 3. インスタンスデータの検証

各インスタンスデータを処理する前に以下の検証を追加:

```python
# インスタンスが空でないか
if not instance:
    logger.warning(f"インスタンス #{idx + 1} が空です")
    continue

# リストまたはタプル型か
if not isinstance(instance, (list, tuple)):
    logger.warning(f"インスタンス #{idx + 1} がリストまたはタプルではありません")
    continue

# 最低2つの要素があるか
if len(instance) < 2:
    logger.warning(f"インスタンス #{idx + 1} の要素数が不足しています")
    continue
```

### 4. 矛盾検出の追加

ユーザー数とインスタンス数の矛盾を検出:

```python
if data['total_occupants'] > 0 and len(data['instances']) == 0:
    logger.error("警告: ユーザーが存在するのにインスタンス情報が取得できませんでした")
    logger.error("これはAPIレスポンスの形式が予想と異なる可能性があります")
```

### 5. デバッグモードの追加

環境変数`DEBUG=true`で詳細なログを有効化:

```python
debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
if debug_mode:
    logger.setLevel(logging.DEBUG)
    logger.info("デバッグモードが有効です")
```

### 6. エラー情報の詳細化

APIエラー時にレスポンス内容を記録:

```python
else:
    logger.error(f"ワールド情報取得失敗: {response.status_code}")
    logger.error(f"レスポンス内容: {response.text[:500]}")
    return None
```

### 7. 例外情報の完全記録

スタックトレースを含む完全なエラー情報を記録:

```python
except Exception as e:
    logger.error(f"ワールド情報取得エラー: {e}", exc_info=True)
    return None
```

## 使用方法

### 通常モード
```bash
python vrchat_instance_monitor.py
```

### デバッグモード
.envファイルに以下を追加:
```bash
DEBUG=true
```

または環境変数で指定:
```bash
DEBUG=true python vrchat_instance_monitor.py
```

## トラブルシューティング

### インスタンス数が0になる場合

1. **デバッグモードを有効化**:
   ```bash
   DEBUG=true python vrchat_instance_monitor.py
   ```

2. **ログファイルを確認**:
   ```bash
   tail -f vrchat_monitor.log
   ```

3. **確認すべきログメッセージ**:
   - "取得したインスタンス数: X"
   - "インスタンスリストが空です"
   - "ワールド情報の全フィールド"
   - "レスポンス内容"

4. **APIレスポンスの確認**:
   - HTTPステータスコードが200か
   - レスポンスが正しいJSON形式か
   - instancesフィールドが存在するか

## 期待される動作

### 正常時
```
環境変数を /path/to/.env から読み込みました
2025-11-20 10:00:00 - INFO - インスタンス監視を開始します（間隔: 10分）
2025-11-20 10:00:00 - INFO - 認証に成功しました
2025-11-20 10:00:01 - INFO - ワールド wrld_xxx のデータを収集中...
2025-11-20 10:00:02 - INFO - ワールド情報: name=Example World, occupants=25
2025-11-20 10:00:02 - INFO - 取得したインスタンス数: 3
2025-11-20 10:00:02 - INFO - インスタンス #1: ID=12345~public, ユーザー数=10
2025-11-20 10:00:03 - INFO - インスタンス #2: ID=67890~friends, ユーザー数=8
2025-11-20 10:00:04 - INFO - インスタンス #3: ID=11111~invite, ユーザー数=7
2025-11-20 10:00:05 - INFO - データ収集完了: 3個のインスタンス情報を取得
2025-11-20 10:00:05 - INFO - データを vrchat_instances.txt に保存しました
```

### 異常時（インスタンス0）
```
2025-11-20 10:00:02 - INFO - ワールド情報: name=Example World, occupants=25
2025-11-20 10:00:02 - WARNING - アクティブなインスタンスが見つかりませんでした
2025-11-20 10:00:02 - WARNING - ワールド情報の全フィールド: ['id', 'name', 'occupants', ...]
2025-11-20 10:00:02 - WARNING - occupants=25, publicOccupants=25
2025-11-20 10:00:02 - ERROR - 警告: ユーザーが存在するのにインスタンス情報が取得できませんでした
2025-11-20 10:00:02 - ERROR - これはAPIレスポンスの形式が予想と異なる可能性があります
```

## まとめ

この修正により、以下が可能になりました。

1. **問題の早期発見**: 詳細なログにより、どの段階で問題が発生しているか特定可能
2. **データの検証**: APIレスポンスの構造を厳密に検証
3. **デバッグの容易化**: デバッグモードで詳細な情報を取得
4. **エラーの追跡**: スタックトレースを含む完全なエラー情報を記録
5. **矛盾の検出**: データの整合性をチェックして異常を検出
