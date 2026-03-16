## m_goods API

FastAPI ベースのシンプルな「goods 管理」API です。PostgreSQL の既存 DB (media / artists / persons / artist_persons / goods / goods_images) にアクセスします。

### セットアップ

- **前提**: Python 3.10 以降推奨、PostgreSQL が起動していて、指定の DB が存在すること

1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

2. `.env` の確認

`DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` を必要に応じて修正してください。デフォルト値は以下です。

- `DB_HOST=localhost`
- `DB_PORT=5432`
- `DB_NAME=tamtdb`
- `DB_USER=tamtuser`
- `DB_PASSWORD=TAMTTAMT`

3. サーバ起動

```bash
uvicorn main:app --reload
```

### 主なエンドポイント

仕様に基づき、以下を実装しています。

- persons / artists / media / goods の一覧取得・追加・更新
- person から関連する media / goods / artist の取得

詳細な I/O 仕様はコード中の FastAPI のルート定義を参照してください。

