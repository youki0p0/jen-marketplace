# Context Scoping — 永続コードマップ（v3.6）

参考: [NanoNets/Graft](https://github.com/NanoNets/Graft)。SWE-bench Verified で
resolve率 54%→66%（+12pt）、ツール呼出-25%/トークン-23%/所要時間-32%という
報告がある（該当リポジトリ自身の実測値。Jenに移植した際の効果は未計測 — 下記「効果不明な部分」参照）。

着想: コーディングエージェントは通常タスクごとに白紙から始まり、1時間前に
マップしたリポジトリを再びゼロから探索し直す。この「再発見」がツール呼出・
トークン・時間の大半を食っている。Graftはこれを、**リポジトリの永続的な
コードグラフを一度作り、各ターン後に差分だけ更新して使い回す**ことで解決する。

## 何が変わるか

**Before（v3.5まで）**: 委譲のたびに jen-scout が対象コードベースを
都度ゼロから探索していた（前回調べたことも活かされない）。

**After（v3.6）**: `.jen/codemap.json` に「ファイル→役割/主要シンボル/
依存関係」の軽量マップを永続化する。

1. 初回はscoutがフルスキャンして構築する（cold start。既存のscout探索と同じコスト）。
2. 以降、対象タスクに関係する箇所だけ**マップから引く**（ゼロから再探索しない）。
3. コードに変更が入るたびに、変更されたファイルとその隣接ノードだけ
   **差分更新**する（全体再構築はしない＝安い。haiku・数ファイル分のみ）。

## `.jen/codemap.json` の形

```json
{
  "files": {
    "src/auth/login.ts": {
      "purpose": "ログインAPIハンドラ",
      "symbols": ["handleLogin", "validateCredentials"],
      "depends_on": ["src/db/users.ts", "src/lib/jwt.ts"],
      "updated_at": "2026-08-20T10:00:00Z"
    }
  }
}
```

- `purpose`: 1行要約。`symbols`: 主要な関数/クラス名。`depends_on`: import/呼び出し先のパス。
- 対象外にしてよいもの: node_modules等の依存パッケージ、生成物、テストフィクスチャの中身。
- サイズが気になる場合はディレクトリ単位で集約してよい（1ファイル1エントリを強制しない）。

## PMOの委譲ルール

**対象エージェント**（コードを読み書き/検収する担当）:
builder, frontend, test, architect, debugger, verifier, strict-verifier,
security-reviewer, ux-critic

**対象外**（広く見る/コード局所化に向かない担当）:
research, product-strategist, ideation, contrarian-reviewer,
monetization-reviewer, release-manager, deep-solver（最終手段なので
スコープを狭めない）, scout自身

手順:

1. 対象エージェントへ委譲する前に、scoutへローカライズを依頼する
   （`.jen/codemap.json` があれば参照のみ、無ければ構築を兼ねて探索する）。
2. 委譲promptには、scoutが返したファイルリスト＋根拠のみを渡す。
   「リポジトリ全体を読んで」という指示はしない。
3. 委譲先が「ローカライズが不足していた」と報告したら、自分で
   Read/Grep/Globしスコープを広げてよい。ただし理由を一言ログする。
   これはループガードの「空転検知」の対象にしない（正当なスコープ拡張のため）。
4. 対象エージェントの作業完了後、scoutに変更ファイルの差分更新をさせる。

## 効果不明な部分（正直に）

- 12pt正解率向上・トークン/時間削減はGraft自身の計測値。Jenのマルチ
  エージェント構成（scoutは元々haiku・別コンテキストで動く設計）に
  そのまま乗るとは限らない。Jen独自の効果測定は行っていない。
- マップの鮮度はheuristic（haikuが書く簡易サマリ）。stale mapによる
  誤誘導は上記のエスケープハッチ（委譲先が自分でスコープを広げる）で吸収する。
  強制はしない — 数値によるhard-stop自動化をしない、というv3.4の不変条件と同じ理由。
- routing-stats.json（自己改善ループ）でscout関連のREJECT/ESCALATEDが
  導入前後で減るかどうかは、利用者側での実測に委ねる。
