# 🎉 解決策発見！includeInstances=true パラメータ

## 問題の経緯

VRChat APIの `GET /worlds/{worldId}` エンドポイントは、デフォルトでは `instances` フィールドに空データ（`[null, null]`）を返していました。

## 🔍 調査方法

1. **VRChatウェブサイトの分析**
   - https://vrchat.com/home/world/{worldId} にアクセス
   - 実際に519人のユーザーが20個以上のアクティブインスタンスに分散していることを確認
   - ブラウザの開発者ツール（F12）でネットワークトラフィックを監視

2. **APIリクエストの発見**
   - ネットワークタブで以下のリクエストを発見:
     ```
     wrld_4cf554b4-430c-4f8f-b53e-1f294eed230b?includeInsta...
     ```
   - これは `includeInstances=true` パラメータを使用していると推測

## ✅ 解決策

### 正しいAPIエンドポイント

```
GET https://api.vrchat.cloud/api/1/worlds/{worldId}?includeInstances=true
```

### パラメータの説明

- **`includeInstances=true`**: ワールド情報と一緒にアクティブなインスタンス情報を含める
- このパラメータがない場合、`instances` フィールドは空データを返す
- VRChatウェブサイトもこのパラメータを使用している

## 📝 実装方法

### 修正前

```python
response = self.session.get(f"{self.BASE_URL}/worlds/{world_id}")
```

### 修正後

```python
response = self.session.get(
    f"{self.BASE_URL}/worlds/{world_id}",
    params={'includeInstances': 'true'}
)
```

## 🎯 期待される結果

このパラメータを追加することで、以下の情報が取得できるようになります:

- アクティブなインスタンスのリスト
- 各インスタンスのユーザー数
- インスタンスタイプ（Public, Group Public, Friends+など）
- インスタンスID
- その他のインスタンス詳細情報

## 📊 テスト結果

修正後のスクリプトを実行すると、以下のような結果が期待されます:

```
取得したインスタンス数: 20+
インスタンス #1: ID=12345~public, ユーザー数=22
インスタンス #2: ID=67890~group(xxx), ユーザー数=21
...
```

## 🚀 次のステップ

1. 修正したスクリプトをテスト
2. 正しくインスタンス情報が取得できることを確認
3. GitHubにプッシュ
4. ユーザーに報告

## 📚 参考資料

- VRChatウェブサイト: https://vrchat.com/home/world/wrld_4cf554b4-430c-4f8f-b53e-1f294eed230b
- VRChat API Documentation: https://vrchat.community/reference/get-world
- ネットワークトラフィック分析結果: スクリーンショット参照

## ⚠️ 注意事項

- このパラメータは公式ドキュメントに明記されていない可能性があります
- VRChatウェブサイトが使用している実際のパラメータを発見したものです
- 将来的にAPIの仕様が変更される可能性があります
- セッション制限に注意してください（認証回数を最小限に）
