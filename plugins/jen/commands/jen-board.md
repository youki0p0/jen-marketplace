---
description: Show the current Jen work board — who is working on what, recent agent-to-agent exchanges, and unresolved failures.
---

Read `.jen/board.md` (and `.jen/tasks.json` if board is missing or stale).
Display to the user:
1. 進行中テーブル（Task / 内容 / 担当 / 状態 / 最終イベント）
2. 直近のやり取り（最新10件、visibility-protocolの書式）
3. 失敗共有（未解決）— 失敗タイプ・引き継ぎ先つき
4. 次に起きる予定のイベント（次の委譲 or 検収 or Human Gate）
If `.jen/board.md` does not exist, say so and offer to initialize it from tasks.json.
