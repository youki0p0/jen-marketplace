---
applyTo: ".jen/**"
---

# Jen 状態ファイルの扱い

`.jen/` は Jen（PMO型オーケストレーター）の実行時状態。触るときは次を守る。

- `.jen/claims.json`（証拠台帳）は**直接編集しない**。必ず
  `python3 .github/hooks/jen/evidence_ledger.py <init|claim-add|attest|run|revise|status>` を使う。
  直接の書き換えは hook で拒否され、封印の不一致として検出される。
- `.jen/inbox.md` は追記専用。既存エントリを編集・要約・整形しない（原文が指示の正）。
- `.jen/logs/` は hook が機械的に書く実ログ。手で書き足さない。
- `.jen/` はコミットしない（`.gitignore` に入れる）。ツールログに secret が載り得る。
