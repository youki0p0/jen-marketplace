# jen-classic (Classic Edition — Fable 不要)

Jen v3 の Fable 非依存版。インストールは親リポジトリの README を参照。
**Fable版 `jen` とは agent 名が同一のため、同時に有効化しないこと。**

- agents/ … 18 subagents（`jen-pmo` と `jen-deep-solver` は **model: opus**。
  Fable版と違い fable は一切使わない。`jen-architect` / `jen-debugger` /
  `jen-strict-verifier` も opus、`jen-scout` が haiku、残り12体が sonnet）
- skills/ … `/jen-classic:jen` ほか5スキル（jen / jen-longrun / jen-repair / jen-review / jen-release）
- commands/ … `/jen-classic:jen-status` `/jen-classic:jen-board`
  `/jen-classic:jen-standup` `/jen-classic:jen-pr` `/jen-classic:jen-audit`
- hooks/ … PreToolUse ガード＋ローカルログ（外部通信なし）
- templates/ … `.jen/` 状態ファイルと各種レポートの雛形

Fable版との差分（Fableの長時間耐性を構造で補償）:
再アンカリング（委譲毎に mission.md 読み直し）/ 1サイクル=1タスク厳守 /
セッションローテーション（8サイクル毎に handoff → 新セッション）/
最終昇格は opus 合議制（architect と debugger の独立仮説を deep-solver が統合）。

⚠️ 導入後は作業リポジトリで `echo '.jen/' >> .gitignore` を実行すること（親 README 参照）。
