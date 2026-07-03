# Long-run Playbook

## Cycle

1. Read `.jen/mission.md` and `.jen/tasks.json`.
2. Pick one small unblocked task.
3. Delegate to the correct specialist.
4. Run relevant quality gate.
5. If pass, update ledger and handoff.
6. If fail, invoke repair.
7. If human gate appears, stop with a clear packet.

## Drift control

- Every task must map to AC.
- Side ideas go to `.jen/ideas.md`.
- Do not expand scope silently.
- Keep changes small.
- Write handoff after each cycle.

## Checkpoint

```bash
git status --short
git diff --stat
bash "${CLAUDE_PLUGIN_ROOT}/skills/jen/scripts/jen_quality_gate.sh"
```

## Fable long-horizon notes (v3)

- Fable 5 は多日規模の自走を想定して設計されている。cycleを止める理由がなければ
  handoff更新→次cycleへ進み続けてよい。
- ただし委譲規律は維持する: PMO(fable)自身が実装を始めたらそれはdrift。
- classifierフォールバック検知: セッションがOpus 4.8へ切り替わった通知が出たら、
  現cycleを完了→handoff更新→新セッション(/model fable)で再開する。
- コストチェックポイント: 5 cycleごとに「fableで処理した工程のうちsonnet以下へ
  委譲できたものはないか」を1行で自己監査し `.jen/decisions.md` に残す。

## Stop conditions

- All AC pass.
- Human Gate needed.
- Same failure repeats 3 times.
- Required external secret/service missing.
- Risk is higher than allowed constraints.
