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

## Visibility (v3.2)

サイクル内の委譲・検収・失敗はやり取り行で逐次表示し、checkpoint毎に
board.md の進行中テーブルを handoff.md へ転記する。長時間の無言運転は禁止。

## Drift check (v3.1)

各checkpointで、直近サイクルの成果物と `.jen/mission.md`（Goal / Non-goals / AC）の
整合を1行で自己評価し handoff.md に記す（例: `drift: OK` / `drift: 逸脱あり - <内容>`）。
逸脱を検出したら次のタスクへ進まず、サイクルを止めて再プランニング
（Mission確認 → タスク再分解）から入り直す。判定に迷う場合は逸脱扱いにして止める。

## Fable long-horizon notes (v3)

- Fable 5 は多日規模の自走を想定して設計されている。cycleを止める理由がなければ
  handoff更新→次cycleへ進み続けてよい。
- ただし委譲規律は維持する: PMO(fable)自身が実装を始めたらそれはdrift。
- classifierフォールバック検知: セッションがOpus 5へ切り替わった通知が出たら、
  現cycleを完了→handoff更新→新セッション(/model fable)で再開する。
- コストチェックポイント: 5 cycleごとに「fableで処理した工程のうちsonnet以下へ
  委譲できたものはないか」を1行で自己監査し `.jen/decisions.md` に残す。

## Loop guards (v3.4)

- 2サイクル連続で台帳無変化 → ブレーカー作動 → 外側リセット（loop-guards.md）。
  リセット2回で解決しなければHuman Gate。
- どの停止でも graceful failure 報告（達成分/未達理由(確定・推測区別)/回復アクション）
  を必ず出す。無言停止禁止。
- compactionやセッション切替で消えて困る決定はその場で decisions.md へ書く。

## Stop conditions

- All AC pass.
- Human Gate needed.
- Same failure repeats 3 times.
- Required external secret/service missing.
- Risk is higher than allowed constraints.
