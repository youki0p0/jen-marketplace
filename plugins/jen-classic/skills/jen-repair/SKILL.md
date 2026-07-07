---
name: jen-repair
description: Jen repair mode for failing tests, broken builds, runtime crashes, verifier rejection, or regressions.
disable-model-invocation: true
argument-hint: "<failure evidence>"
---

# Jen Repair

1. Fix the reproduction command or steps.
2. Classify the failure.
3. Use `jen-debugger` for unknown/root-cause work or `jen-test` for test-specific failures.
4. Apply minimal fix.
5. Add regression test if possible.
6. Run relevant quality gate.
7. Use `jen-verifier` or `jen-strict-verifier` for acceptance.
8. Record failure and fix in `.jen/verification.md` and `.jen/handoff.md`.

## Loop guards (v3.4)

同一の修正を2回試して失敗したら、3回目は禁止。仮説を変えるか昇格する。
修正試行ごとに「前回と何を変えたか」を1行で明示すること。

## Lessons (v3.3)

修復が検収を通ったら、必ず `.jen/lessons.md` へ教訓を1エントリ追記する
（書式: references/lessons-protocol.md）。着手前には lessons.md の
同種タスクの再発防止ルールを読み、既知の過ちを繰り返さないこと。
