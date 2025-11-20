# VRChat API調査結果

## 問題の本質

VRChat APIの`GET /worlds/{worldId}`エンドポイントは、認証済みでも`instances`フィールドに実際のインスタンス情報を返さない仕様になっています。

### APIレスポンス例

```json
{
  "occupants": 47,
  "publicOccupants": 46,
  "privateOccupants": 1,
  "instances": [
    [null, null]
  ]
}
```

ドキュメントの記載:
> "Works unauthenticated but when so will always return 0 for certain fields."

## 解決方法

### 方法1: Get Instance API を使用（推奨）

`GET /instances/{worldId}:{instanceId}` エンドポイントを使用すると、個別のインスタンス情報を取得できます。

**レスポンス例**:
```json
{
  "n_users": 6,
  "capacity": 8,
  "full": false,
  "platforms": {
    "android": 1,
    "ios": 1,
    "standalonewindows": 5
  },
  "type": "hidden"
}
```

**問題点**: インスタンスIDのリストを事前に知る必要がある

### 方法2: VRChatウェブサイトをスクレイピング

VRChatの公式ウェブサイト（https://vrchat.com/home/world/{worldId}）には、アクティブなインスタンス情報が表示されています。

**利点**:
- インスタンスIDのリストを取得できる
- ユーザー数も表示されている

**欠点**:
- 公式APIではない
- HTML構造が変更される可能性がある
- レート制限が厳しい可能性

### 方法3: 別のAPIエンドポイントを探す

VRChat APIには他にもエンドポイントがある可能性があります。

## 推奨アプローチ

**VRChatウェブサイトから情報を取得する**

1. `https://vrchat.com/home/world/{worldId}` にアクセス
2. ページからインスタンス情報を抽出
3. 必要に応じて個別のインスタンスAPIを呼び出す

これにより、以下の情報が取得できます:
- アクティブなインスタンスのリスト
- 各インスタンスのユーザー数
- インスタンスタイプ（public, friends+, etc.）
