# m_goods システム仕様書（DB・API）

このドキュメントは、PostgreSQL 上の DB レイアウトと FastAPI で提供する REST API の仕様を、生成AIを含む他システムが一意に解釈できるよう構造化して記述したものです。

---

## 1. データベースレイアウト（PostgreSQL）

### 1.1 前提

- **RDBMS**: PostgreSQL
- **スキーマ**: `public`（省略可）
- **用語**: 「媒体」= media、「アーティスト」= artist、「人物」= person、「商品」= goods

### 1.2 テーブル一覧とリレーション

- **media** … 媒体（CD/BD/DVD など）のマスタ
- **artists** … アーティストのマスタ
- **persons** … 人物のマスタ（声優・出演者など）
- **artist_persons** … アーティストと人物の多対多の中間テーブル
- **goods** … 商品（媒体×アーティストの組み合わせ＋タイトル等）
- **goods_images** … 商品に紐づく画像（1商品あたり0件以上）

**参照関係の要約:**

- `goods.media_id` → `media.id`
- `goods.artist_id` → `artists.id`
- `artist_persons.artist_id` → `artists.id`
- `artist_persons.person_id` → `persons.id`
- `goods_images.goods_id` → `goods.id`

---

### 1.3 テーブル定義（カラム・型・制約）

#### 1.3.1 media

| カラム名    | 型                         | Nullable | デフォルト | 説明           |
|------------|----------------------------|----------|------------|----------------|
| id         | integer                    | NOT NULL | nextval    | 主キー         |
| name       | character varying          | NOT NULL | -          | 媒体名         |
| created_at | timestamp without time zone| NOT NULL | now()      | 作成日時       |
| updated_at | timestamp without time zone| NOT NULL | now()      | 更新日時       |

- **主キー**: `id`
- **インデックス**: `id`, `name`
- **被参照**: `goods.media_id`

---

#### 1.3.2 artists

| カラム名    | 型                         | Nullable | デフォルト | 説明           |
|------------|----------------------------|----------|------------|----------------|
| id         | integer                    | NOT NULL | nextval    | 主キー         |
| name       | character varying          | NOT NULL | -          | アーティスト名 |
| created_at | timestamp without time zone| NOT NULL | now()      | 作成日時       |
| updated_at | timestamp without time zone| NOT NULL | now()      | 更新日時       |

- **主キー**: `id`
- **インデックス**: `id`, `name`
- **被参照**: `artist_persons.artist_id`, `goods.artist_id`

---

#### 1.3.3 persons

| カラム名    | 型                         | Nullable | デフォルト | 説明     |
|------------|----------------------------|----------|------------|----------|
| id         | integer                    | NOT NULL | nextval    | 主キー   |
| name       | character varying          | NOT NULL | -          | 人物名   |
| created_at | timestamp without time zone| NOT NULL | now()      | 作成日時 |
| updated_at | timestamp without time zone| NOT NULL | now()      | 更新日時 |

- **主キー**: `id`
- **インデックス**: `id`, `name`
- **被参照**: `artist_persons.person_id`

---

#### 1.3.4 artist_persons

| カラム名   | 型                         | Nullable | デフォルト | 説明           |
|------------|----------------------------|----------|------------|----------------|
| id         | integer                    | NOT NULL | nextval    | 主キー         |
| artist_id  | integer                    | NOT NULL | -          | FK → artists.id |
| person_id  | integer                    | NOT NULL | -          | FK → persons.id |
| created_at | timestamp without time zone| NOT NULL | now()      | 作成日時       |

- **主キー**: `id`
- **外部キー**: `artist_id` → `artists(id)`, `person_id` → `persons(id)`
- **インデックス**: `id`, `artist_id`, `person_id`
- **制約**: (artist_id, person_id) の組み合わせは一意であることが望ましい（実装で UniqueConstraint を付与している）

---

#### 1.3.5 goods

| カラム名     | 型                         | Nullable | デフォルト | 説明           |
|--------------|----------------------------|----------|------------|----------------|
| id           | integer                    | NOT NULL | nextval    | 主キー         |
| media_id     | integer                    | NOT NULL | -          | FK → media.id  |
| artist_id    | integer                    | NOT NULL | -          | FK → artists.id|
| title        | character varying          | NOT NULL | -          | タイトル       |
| release_date | date                       | NOT NULL | -          | 発売日         |
| memo         | text                       | NULL     | -          | メモ           |
| is_deleted   | boolean                    | NOT NULL | -          | 論理削除フラグ |
| created_at   | timestamp without time zone| NOT NULL | now()      | 作成日時       |
| updated_at   | timestamp without time zone| NOT NULL | now()      | 更新日時       |
| is_owned     | boolean                    | NOT NULL | false      | 所持フラグ     |
| code_number  | character varying          | NULL     | -          | 品番等         |

- **主キー**: `id`
- **外部キー**: `media_id` → `media(id)`, `artist_id` → `artists(id)`
- **インデックス**: `id`, `media_id`, `artist_id`, `release_date`, `is_deleted`
- **被参照**: `goods_images.goods_id`

---

#### 1.3.6 goods_images

| カラム名      | 型                         | Nullable | デフォルト | 説明         |
|---------------|----------------------------|----------|------------|--------------|
| id            | integer                    | NOT NULL | nextval    | 主キー       |
| goods_id      | integer                    | NOT NULL | -          | FK → goods.id|
| image_data    | bytea                      | NOT NULL | -          | 画像バイナリ |
| image_type    | character varying          | NOT NULL | -          | MIME 等      |
| display_order | integer                    | NOT NULL | -          | 表示順       |
| created_at    | timestamp without time zone| NOT NULL | now()      | 作成日時     |

- **主キー**: `id`
- **外部キー**: `goods_id` → `goods(id)`
- **インデックス**: `id`, `goods_id`, `display_order`

---

## 2. API 仕様（REST / FastAPI）

- **ベースURL**: デプロイ環境に依存（例: `http://localhost:8000`）
- **Content-Type**: リクエスト・レスポンスとも JSON（画像データは Base64 等でエンコードして扱う実装が一般的）
- **エラー**: 4xx/5xx で HTTP ステータスと `detail` 等のメッセージを返す。

以下、エンドポイントごとに「番号」「メソッド・パス」「入力」「出力」「処理内容」を定義する。

---

### API-1: person一覧取得

- **メソッド・パス**: `GET /persons`
- **入力**: なし（クエリパラメータなし）
- **出力**: オブジェクトの配列。各要素は `{ "id": number, "name": string }`
- **処理**: `persons` テーブルを検索し、`id` と `name` のリストを返す。

---

### API-2: 関連 media 一覧取得

- **メソッド・パス**: `POST /persons/related-media`
- **入力（Body）**: `{ "person_id": number }`
- **出力**: オブジェクトの配列。各要素は `{ "id": number, "name": string }`。**重複なし**。
- **処理**:
  1. `artist_persons` を検索し、`person_id` が入力の `person_id` と一致する `artist_id` の集合を取得する。
  2. `goods` を検索し、`artist_id` が 1 の集合に含まれ、かつ `is_deleted` が `false` であるレコードの `media_id` の集合を取得する。
  3. `media` を検索し、`id` が 2 の集合に含まれるレコードの `id` と `name` を重複なく返す。

---

### API-3: 関連 goods 一覧取得

- **メソッド・パス**: `POST /persons/related-goods`
- **入力（Body）**: `{ "person_id": number, "media_ids": number[] }`
- **出力**: オブジェクトの配列。各要素は次のフィールドを持つ。
  - `goods_id` (number): goods.id
  - `media_id` (number): goods.media_id
  - `artist_id` (number): goods.artist_id
  - `media_name` (string): media.name
  - `artist_name` (string): artists.name
  - `title` (string): goods.title
  - `release_date` (string, date): goods.release_date
  - `memo` (string | null): goods.memo
  - `is_owned` (boolean): goods.is_owned
  - `code_number` (string | null): goods.code_number
  - `image_type` (string | null): goods_images.image_type（1件目または代表1件）
  - `image_data` (binary/Base64 等 | null): goods_images.image_data（同上）
- **処理**:
  1. `artist_persons` を検索し、`person_id` が入力の `person_id` と一致する `artist_id` の集合を取得する。
  2. `goods` を検索し、`artist_id` が 1 の集合に含まれ、`media_id` が入力の `media_ids` に含まれ、かつ `is_deleted` が `false` であるレコードを取得する。
  3. 2 の結果と `media`・`artists`・`goods_images`（1件目または display_order 順の先頭など）を結合し、上記の形のリストを返す。

---

### API-4: 関連 artist 一覧取得

- **メソッド・パス**: `POST /persons/related-artists`
- **入力（Body）**: `{ "person_id": number }`
- **出力**: オブジェクトの配列。各要素は `{ "id": number, "name": string }`（artists の id, name）
- **処理**:
  1. `artist_persons` を検索し、`person_id` が入力の `person_id` と一致する `artist_id` の集合を取得する。
  2. `artists` を検索し、`id` が 1 の集合に含まれるレコードの `id` と `name` のリストを返す。

---

### API-5: person 追加

- **メソッド・パス**: `POST /persons`
- **入力（Body）**: `{ "name": string }`
- **出力**: `{ "id": number, "name": string }`（登録された persons のレコード）
- **処理**: `persons` に、入力の `name` でレコードを1件追加する。`created_at`/`updated_at` は DB のデフォルト（now()）でよい。

---

### API-6: person 更新

- **メソッド・パス**: `PUT /persons/{person_id}`
- **入力**: パス `person_id` (number)、Body `{ "id": number, "name": string }`。パスの `person_id` と Body の `id` は一致させること。
- **出力**: `{ "id": number, "name": string }`（更新後の persons のレコード）
- **処理**: `persons` の `id` が `person_id`（および Body の `id`）と一致するレコードの `name` を入力の `name` に更新する。該当がなければ 404 を返す。

---

### API-7: artist 一覧取得

- **メソッド・パス**: `GET /artists`
- **入力**: なし
- **出力**: オブジェクトの配列。各要素は `{ "id": number, "name": string }`（artists の id, name）
- **処理**: `artists` を検索し、`id` と `name` のリストを返す。

---

### API-8: artist 情報取得（詳細）

- **メソッド・パス**: `GET /artists/{artist_id}`
- **入力**: パス `artist_id` (number)
- **出力**: `{ "name": string, "persons": [ { "id": number, "name": string }, ... ] }`  
  - `name`: artists.name  
  - `persons`: 当該 artist に紐づく persons の id と name のリスト
- **処理**:
  1. `artists` を検索し、`id` が `artist_id` と一致するレコードを取得する。なければ 404。
  2. `artist_persons` を検索し、`artist_id` が `artist_id` と一致するレコードの `person_id` を取得する。
  3. `persons` を検索し、2 の `person_id` に一致する id と name を取得する。
  4. 1 の name と 3 のリストを上記の形で返す。

---

### API-9: artist 追加

- **メソッド・パス**: `POST /artists`
- **入力（Body）**: `{ "name": string }`
- **出力**: `{ "id": number, "name": string }`（登録された artists のレコード）
- **処理**: `artists` に、入力の `name` でレコードを1件追加する。

---

### API-10: artist 更新

- **メソッド・パス**: `PUT /artists/{artist_id}`
- **入力**: パス `artist_id` (number)、Body `{ "id": number, "name": string, "person_ids": number[] }`。パスの `artist_id` と Body の `id` は一致させること。
- **出力**: `{ "id": number, "name": string }`（更新後の artists のレコード）
- **処理**:
  1. `artists` の `id` が `artist_id` と一致するレコードの `name` を入力の `name` に更新する。該当がなければ 404。
  2. `artist_persons` について、`artist_id` が `artist_id` であるレコードと、入力の `person_ids` を比較する。
     - 入力の (artist_id, person_id) の組のうち、DB に存在しないものは **追加** する。
     - DB に存在するが入力の `person_ids` に含まれない `person_id` は **削除** する。

---

### API-11: media 一覧取得

- **メソッド・パス**: `GET /media`
- **入力**: なし
- **出力**: オブジェクトの配列。各要素は `{ "id": number, "name": string }`
- **処理**: `media` を検索し、`id` と `name` のリストを返す。

---

### API-12: media 追加

- **メソッド・パス**: `POST /media`
- **入力（Body）**: `{ "name": string }`
- **出力**: `{ "id": number, "name": string }`（登録された media のレコード）
- **処理**: `media` に、入力の `name` でレコードを1件追加する。

---

### API-13: media 更新

- **メソッド・パス**: `PUT /media/{media_id}`
- **入力**: パス `media_id` (number)、Body `{ "id": number, "name": string }`。パスの `media_id` と Body の `id` は一致させること。
- **出力**: `{ "id": number, "name": string }`（更新後の media のレコード）
- **処理**: `media` の `id` が `media_id` と一致するレコードの `name` を入力の `name` に更新する。該当がなければ 404。

---

### API-14: goods 1件取得

- **メソッド・パス**: `GET /goods/{goods_id}`
- **入力**: パス `goods_id` (number)
- **出力**: オブジェクト 1 件。API-3 の出力要素と同じ形（`goods_id`, `media_id`, `artist_id`, `media_name`, `artist_name`, `title`, `release_date`, `memo`, `is_owned`, `code_number`, `image_type`, `image_data`）。該当する goods が存在しなければ 404 を返す。
- **処理**: `goods` の `id` が `goods_id` と一致するレコードを、`media`・`artists`・`goods_images`（display_order 順の先頭 1 件）と結合して上記の形で返す。

---

### API-15: goods 追加

- **メソッド・パス**: `POST /goods`
- **入力（Body）**: 以下。必須は `media_id`, `artist_id`, `title`。
  - `media_id` (number, 必須)
  - `artist_id` (number, 必須)
  - `title` (string, 必須)
  - `release_date` (string, date, 任意。省略時は当日)
  - `memo` (string, 任意。省略時は `""`)
  - `is_owned` (boolean, 任意。省略時は false)
  - `code_number` (string, 任意。省略時は `""`)
  - `image_type` (string, 任意)
  - `image_data` (binary/Base64 等, 任意)
- **出力**: `{ "id": number }`（登録された goods の id）
- **処理**:
  - `goods` に 1 件挿入する。`is_deleted` が指定されなければ `false`、`is_owned` が指定されなければ `false`。`release_date` 省略時は当日、`memo` 省略時は `""`、`code_number` 省略時は `""` を登録する。
  - `goods_images` には、`image_type` と `image_data` の**両方が**指定された場合のみレコードを追加する（1件目として display_order=1 等でよい）。

---

### API-16: goods 更新

- **メソッド・パス**: `PUT /goods/{goods_id}`
- **入力**: パス `goods_id` (number)、Body に `id` (number) および API-15 と同様のフィールド（`media_id`, `artist_id`, `title` 必須）。パスの `goods_id` と Body の `id` は一致させること。
- **出力**: `{ "id": number }`（更新した goods の id）
- **処理**:
  - `goods` の `id` が `goods_id` と一致するレコードを、入力の内容で更新する。該当がなければ 404。
  - `goods_images` についても、入力に `image_type` と `image_data` が両方あればそれで更新または1件追加、そうでなければ既存の画像レコードを削除する等、実装方針に合わせて更新する。

---

## 3. エンドポイント一覧（早見）

| 番号 | メソッド | パス                         | 概要               |
|------|----------|------------------------------|--------------------|
| 1    | GET      | /persons                     | person一覧取得     |
| 2    | POST     | /persons/related-media       | 関連media一覧取得 |
| 3    | POST     | /persons/related-goods       | 関連goods一覧取得 |
| 4    | POST     | /persons/related-artists     | 関連artist一覧取得|
| 5    | POST     | /persons                     | person追加         |
| 6    | PUT      | /persons/{person_id}         | person更新         |
| 7    | GET      | /artists                     | artist一覧取得     |
| 8    | GET      | /artists/{artist_id}         | artist情報取得    |
| 9    | POST     | /artists                     | artist追加         |
| 10   | PUT      | /artists/{artist_id}         | artist更新         |
| 11   | GET      | /media                       | media一覧取得      |
| 12   | POST     | /media                       | media追加          |
| 13   | PUT      | /media/{media_id}            | media更新          |
| 14   | GET      | /goods/{goods_id}            | goods 1件取得      |
| 15   | POST     | /goods                       | goods追加          |
| 16   | PUT      | /goods/{goods_id}            | goods更新          |

---

## 4. 環境・接続

- **DB 接続情報**は `.env` で管理する。
- 代表的な変数名と初期値の例:
  - `DB_HOST=localhost`
  - `DB_PORT=5432`
  - `DB_NAME=tamtdb`
  - `DB_USER=tamtuser`
  - `DB_PASSWORD=TAMTTAMT`

この仕様書は、上記の DB レイアウトと API の挙動を一意に解釈するための参照として利用できます。
