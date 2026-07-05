# Jen v3 — Fable Edition 🎼

**指揮は Fable、実行は安く。** ゴールを渡すだけで、分解・委譲・検証・差し戻し・リリース準備まで管理する PMO 型 AI 開発オーケストレーター（Claude Code プラグイン）。

呼び名：Jen / Jenifer / Jenny / ジェン / ジェニー / ジェニファー

```
┌─────────────────────────────────────────────┐
│  fable   jen-pmo（指揮）/ architect / jen-deep-solver │  ← 計画・設計・最終昇格
├─────────────────────────────────────────────┤
│  opus    debugger / strict-verifier          │
├─────────────────────────────────────────────┤
│  sonnet  builder / frontend / test / research / reviewers │
├─────────────────────────────────────────────┤
│  haiku   scout                               │  ← 下調べ（read-only）
└─────────────────────────────────────────────┘
昇格ラダー: haiku → sonnet → opus → fable → 人間へ返す
```

## なにが嬉しいの？

- **ゴールだけ渡せばいい** — Jen が Mission Brief / 受入条件 / タスク台帳を作り、18体の専門エージェントに振り分ける
- **「完成」を雰囲気で言わない** — Verifier（検収専任）が ACCEPT するまで完了扱いにしない。実装者と検証者を分離
- **コストが暴れない** — 単価の高い Fable 5 は指揮（jen-pmo）・設計（jen-architect）・最終昇格先（jen-deep-solver）の3箇所のみ。トークンを大量に消費する実装・探索は haiku / sonnet
- **デザインは発明しない** — Claude Design（claude.ai/design）のデザインシステムを正本とし、`/design-sync` で同期。jen-frontend は正本に忠実に実装する
- **勝手に壊さない** — DB破壊・deploy・secret・auth/payment は Human Gate で必ず停止。危険コマンドは PreToolUse hook でブロック
- **多日自走できる** — longrun モードはチェックポイント・handoff・品質ゲートを挟みながら完了まで回り続ける（Fable 5 の長時間自律性を活用）

## v3.2 の新要素 — 作業の可視化

エージェント同士のやり取り（委譲→完了→検収→差し戻し→昇格）が1行フォーマットでリアルタイムに流れ、`.jen/board.md` に「誰が何を担当中か・未解決の失敗と引き継ぎ先」が常に残ります。`/jen:jen-board` でいつでも確認可能。**失敗は隠さず、理由と引き継ぎ先つきで共有**——ブラックボックスにしないのがJenの方針です。

```
🎼 jen-pmo ▶ jen-builder     T-014「ログイン画面実装」を委譲
🔨 jen-builder ✔ 完了 ▶ jen-verifier   T-014 検収を依頼
🔍 jen-verifier ✖ REJECT[format] ▶ jen-builder   差し戻し: エラー状態UI未実装
```

## v3.1 の新要素 — 自己改善ループ

実行するたびに賢くなる、を安全側に倒して実装：ルーティング学習（担当×検収結果の記録・参照）、REJECT失敗タイプのタグ付け、longrunのドリフト自己監視、スキル候補の自動提案（**採用判断は人間**）。統計と自己評価はあくまで参考情報で、昇格ラダー・Human Gate・二値検収を上書きしません。詳細は [CHANGELOG.md](CHANGELOG.md)。

## インストール

```bash
# Claude Code v2.1.170+ が必要
claude update
```

Claude Code 内で：

```
/plugin marketplace add youki0p0/jen-marketplace
/plugin install jen@jen-marketplace
/model fable
```

以上。リポジトリに何も展開しません（状態ファイル `.jen/` は実行時に作られます）。

> ⚠️ `CLAUDE_CODE_SUBAGENT_MODEL` 環境変数が設定されていると各エージェントの model 指定を上書きします。`unset` してください。

## 使い方

```
/jen:jen conduct
Goal: サインアップ後のオンボーディング画面を改善し、
      初回ユーザーが3分以内に主要機能へ到達できるようにする。
Must Have: 既存デザイントークン準拠 / モバイル対応 / 既存テストを壊さない
Out of Scope: 課金導線の変更 / DB schema 変更
Acceptance Criteria:
- 初回画面に次アクションが表示される
- 空状態とエラー状態がある
- lint / typecheck / test が通る
```

※ プラグイン経由のためスキル・コマンドは `/jen:` 名前空間になります。

| モード | 用途 |
|---|---|
| `route` | 小タスク。1工程ずつ振って verifier 合格まで |
| `conduct` | 中〜大規模。DAG 分解し独立工程は並列 |
| `repair` | 失敗・バグの切り分け → 最小修正 → 回帰 → 検収 |
| `review` | UX / セキュリティ / 反対意見 / 収益化レビュー |
| `release` | PR 要約・検証パケット・ロールバック。deploy は人間承認で停止 |
| `longrun` | チェックポイントと品質ゲートを挟み完了まで自走 |

詳しくは [docs/jen-v3-usage-guide.pdf](docs/jen-v3-usage-guide.pdf)（日本語・7ページ）へ。

## 中身の透明性（インストール前に読んでほしい）

サードパーティのスキル/プラグインは中身を確認してから入れるのが原則です。Jen は全部読めます：

- **外部通信なし** — hooks / scripts に curl・fetch・外部送信は一切ありません（[hooks/](plugins/jen/hooks/) は40行程度の Python なので目視できます）
- **hooks がやること** — `pre_tool_guard.py`（`rm -rf /`・force push・publish・deploy・DROP TABLE 等を**ブロックする側**）、`post_tool_log.py` / `stop_append_summary.py`（`.jen/logs/` へのローカル JSONL 追記のみ）
- **secret を要求しない** — APIキー・トークン入力を求める箇所はありません
- **書き込み先** — リポジトリ内の `.jen/`（状態・ログ）のみ。`.gitignore` 推奨エントリは同梱

## 構成

```
plugins/jen/
├─ agents/      18体（pmo, scout, research, builder, frontend, test,
│                architect, debugger, verifier×2, reviewer×4,
│                strategist, ideation, release-manager, deep-solver）
├─ skills/      jen / jen-longrun / jen-repair / jen-review / jen-release
├─ commands/    jen-status / jen-standup / jen-pr
├─ hooks/       破壊的操作ガード＋ローカルログ
└─ templates/   memory / prompts / report テンプレート
```

## ライセンス

MIT — 商用含め自由に使えます。改変・再配布時は著作権表示を残してください。

---

*Jen v1 の Sakana Fugu 型ルーティング思想を PMO 運用へ拡張した v2 を経て、v3 で Claude Fable 5 前提のモデル階層に再設計。設計の変遷は [docs/JEN_V3_DESIGN.md](docs/JEN_V3_DESIGN.md) に。*
