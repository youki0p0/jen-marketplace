---
name: jen-longrun
description: Long-running Jen PMO autonomous development loop. Use when the user wants Claude Code to keep working toward completion with checkpoints, quality gates, repair, and handoff.
disable-model-invocation: true
argument-hint: "<goal and constraints>"
---

# Jen Longrun (v3 / Classic Edition — Fable不使用)

長時間自走サイクル。**v3.8以降、メインセッションは伝言役**であり、PMOは
`jen-pmo` subagent（frontmatter で `model: opus` 固定、セッションのモデルとは独立）が担う。
したがってメインセッションを `/model opus` にする必要はない — 原文を要約せず
`.jen/inbox.md` へ保全して jen-pmo へ渡すことだけが仕事（references/relay-protocol.md）。

**Classic は Fable を使わない。** 昇格ラダーは haiku → sonnet → opus → opus合議
(jen-deep-solver) で止まる。Fable の長時間一貫性をモデルで持てないぶん、構造で補償する
（references/model-tiering.md「Fableとの差分と構造補償」）:

- **1サイクル = タスク1つ**を厳守する。まとめ処理はドリフトの温床。
- 委譲のたびに `.jen/mission.md` の Goal / Non-goals / AC を読み直す（再アンカリング）。
- **8サイクル毎**、またはコンテキスト圧迫・応答品質低下を感じたら、`.jen/handoff.md` を
  更新して新セッションで再開する。Fable版の「止める理由がなければ回し続けてよい」は
  Classic では適用しない。

1. Create/update `.jen/mission.md` with Goal, Non-goals, Constraints, AC, Human Gates.
2. Create/update `.jen/tasks.json`.
3. Work in small cycles.
4. Delegate implementation to specialists.
5. Run quality gates.
6. Repair failures up to 3 loops.
7. Update `.jen/handoff.md` after each cycle.
8. Stop only when all AC pass, a Human Gate is required, or repeated failure blocks progress.

Do not deploy, alter secrets, perform destructive DB changes, or expand scope without human approval.
