---
description: Run an independent behavior audit — check what Jen actually did (from hook-recorded logs) against what it self-reported.
---

jen-scoutへ以下を依頼する（PMOを経由せず直接でよい。これがPMOの自己申告に
依存しない唯一の独立チェック経路）:

1. `.jen/skillmap.json` を構築/更新し、agents/skills/commands/referencesの
   整合性チェック結果（`issues`）を表示する。
2. `.jen/logs/tool-events.jsonl` と `.jen/logs/stop-events.jsonl`（hookが
   機械的に記録した実ログ）を、`.jen/board.md` / `.jen/routing-stats.json` /
   `.jen/decisions.md`（PMOの自己申告）と突き合わせ、`.jen/audit.md` を作成/更新する。
3. 各観点（可視化コンプライアンス / Ratio Guard整合性 / コンテキストスコープ
   遵守 / ループガード遵守）を 準拠 / 逸脱（証跡付き） / 判定不能 の3値で表示する。

詳細: `references/behavior-audit.md`。
このコマンドは強制停止や自動修正をしない。逸脱が見つかった場合は
ユーザーへそのまま報告し、対応（PMOへの差し戻し、Human Gate化など）は
ユーザー/PMOの判断に委ねる。
