# Jen v3 — Fable Edition 🎼

**指揮は Fable、実行は安く。** ゴールを渡すだけで、分解・委譲・検証・差し戻し・リリース準備まで管理する PMO 型 AI 開発オーケストレーター（Claude Code プラグイン）。

呼び名：Jen / Jenifer / Jenny / ジェン / ジェニー / ジェニファー

```
┌─────────────────────────────────────────────┐
│  fable   jen-pmo（指揮）/ jen-deep-solver    │  ← 計画維持・委譲・自己検証
├─────────────────────────────────────────────┤
│  opus    architect / debugger / strict-verifier │
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
- **コストが暴れない** — 単価の高い Fable 5 は指揮（jen-pmo）と最終昇格先（jen-deep-solver）の2箇所のみ。手足は haiku / sonnet
- **勝手に壊さない** — DB破壊・deploy・secret・auth/payment は Human Gate で必ず停止。危険コマンドは PreToolUse hook でブロック
- **多日自走できる** — longrun モードはチェックポイント・handoff・品質ゲートを挟みながら完了まで回り続ける（Fable 5 の長時間自律性を活用）

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
