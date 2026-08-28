# jen (Fable Edition)

Jen v3 本体。インストールは親リポジトリの README を参照。

- agents/ … 18 subagents（`jen-pmo` と `jen-deep-solver` が model: fable、
  `jen-architect` / `jen-debugger` / `jen-strict-verifier` が opus、
  `jen-scout` が haiku、残り12体が sonnet）
- skills/ … `/jen:jen` ほか5スキル（jen / jen-longrun / jen-repair / jen-review / jen-release）
- commands/ … `/jen:jen-status` `/jen:jen-board` `/jen:jen-standup` `/jen:jen-pr` `/jen:jen-audit`
- hooks/ … PreToolUse ガード＋ローカルログ（外部通信なし）
- templates/ … `.jen/` 状態ファイルと各種レポートの雛形

⚠️ `jen-classic` とは agent 名が同一のため同時に有効化しないこと。
⚠️ 導入後は作業リポジトリで `echo '.jen/' >> .gitignore` を実行すること（親 README 参照）。
