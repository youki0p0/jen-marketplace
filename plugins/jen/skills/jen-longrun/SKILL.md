---
name: jen-longrun
description: Long-running Jen PMO autonomous development loop. Use when the user wants Claude Code to keep working toward completion with checkpoints, quality gates, repair, and handoff.
disable-model-invocation: true
argument-hint: "<goal and constraints>"
---

# Jen Longrun (v3 / Fable Edition)

長時間自走サイクル。**v3.8以降、メインセッションは伝言役**であり、PMOは
`jen-pmo` subagent（frontmatter で `model: fable` 固定、セッションのモデルとは独立）が担う。
したがってメインセッションを `/model fable` にする必要はない — 原文を要約せず
`.jen/inbox.md` へ保全して jen-pmo へ渡すことだけが仕事（references/relay-protocol.md）。

多日規模の自走は Claude Fable 5.1 の長時間一貫性に依存する。実行は安い worker へ委譲し、
昇格は haiku → sonnet → opus → fable (jen-deep-solver) のラダーのみを通る。fable 直行は禁止。

1. Create/update `.jen/mission.md` with Goal, Non-goals, Constraints, AC, Human Gates.
2. Create/update `.jen/tasks.json`.
3. Work in small cycles.
4. Delegate implementation to specialists.
5. Run quality gates.
6. Repair failures up to 3 loops.
7. Update `.jen/handoff.md` after each cycle.
8. Stop only when all AC pass, a Human Gate is required, or repeated failure blocks progress.

Do not deploy, alter secrets, perform destructive DB changes, or expand scope without human approval.
