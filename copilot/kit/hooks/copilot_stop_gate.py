#!/usr/bin/env python3
"""Jen for Copilot — 完了ゲート（agentStop hook アダプタ）.

Claude Code 版の `stop_gate.py` は **exit 2** で完了を差し戻す。
しかし Copilot の `agentStop` では exit 2 は「警告」扱いで、**ターンは止まらない**
（hooks-reference「Exit codes for command hooks」）。止めるには stdout に

    {"decision": "block", "reason": "<次のターンのプロンプト>"}

を1つだけ出す必要がある（「agentStop / subagentStop decision control」）。

このアダプタは判定ロジックを持たない。判定は従来どおり `stop_gate.py`
（→ `evidence_ledger.py gate`）に任せ、**出力形式だけを Copilot へ翻訳する**。
判定を二重実装しないのは、Claude 版と Copilot 版でゲートの意味がずれないようにするため。

## Copilot 固有の制約への対処

1. **連続 block の上限**: CLI は block が8回続くとフックを無視してターンを終える
   （runaway guard）。黙って突破されるより先に、こちらで `MAX_CONSECUTIVE` 回で
   諦め、**ゲートを通らずに終わったことを記録する**（`gated:false, reason:block_cap`）。
   行動監査（jen-audit）がこれを拾える。穴を黙って残さず、見えるようにしてから残す。
2. **cloud agent の時間**: block で強制した追加ターンもジョブのタイムアウトに数えられる。
   上限を8より小さくしているのはそのため。
3. **subagentStop には使わない**: worker の完了はミッションの完了ではない。
   このスクリプトは `agentStop`（メインエージェント）にだけ登録する。
4. **アダプタ自身の故障**: agentStop の非ゼロ終了は fail-open（ログのみ）なので、
   例外時は何も出さずに終わる。ただし記録は試みる。

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STOP_GATE = HERE / "stop_gate.py"
STATE = Path(".jen/logs/copilot-stop-state.json")
LOG = Path(".jen/logs/stop-events.jsonl")
# CLI の runaway guard（8回）より手前で止める。
MAX_CONSECUTIVE = 6
# stop_gate.py のメッセージは Claude 版のパスを案内するので、Copilot 版の配置へ読み替える
PATH_REWRITES = (
    ("${CLAUDE_PLUGIN_ROOT}/hooks/", ".github/hooks/jen/"),
    ("$CLAUDE_PLUGIN_ROOT/hooks/", ".github/hooks/jen/"),
)


def record(entry: dict) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        entry["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        entry["surface"] = "copilot"
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"consecutive_blocks": 0}


def save_state(state: dict) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


def rewrite(text: str) -> str:
    for old, new in PATH_REWRITES:
        text = text.replace(old, new)
    return text


def main() -> int:
    if not Path(".jen").is_dir():
        # Jen を使っていないセッション。.github/hooks はリポジトリの全セッションで発火するので、
        # ここで何かを書くと .jen/ が生えて他の hook の opt-in 条件を満たしてしまう。
        return 0
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}
    forced = bool(payload.get("stop_hook_active"))

    state = load_state()
    if not forced:
        # ユーザー起点の新しいターン。連続カウンタを戻す。
        state["consecutive_blocks"] = 0

    proc = subprocess.run([sys.executable, str(STOP_GATE)], input=raw,
                          capture_output=True, text=True, check=False)

    if proc.returncode == 0:
        state["consecutive_blocks"] = 0
        save_state(state)
        if proc.stderr.strip():
            sys.stderr.write(rewrite(proc.stderr))
        return 0

    if state.get("consecutive_blocks", 0) >= MAX_CONSECUTIVE:
        # これ以上 block しても CLI の上限で無視されるだけ。
        # 黙って通さず、通さなかったことを記録してから終わらせる。
        record({"event": "agentStop", "gated": False, "reason": "block_cap",
                "consecutive_blocks": state["consecutive_blocks"]})
        # カウンタは戻さない。同じ強制継続の連鎖が続く限り block しない。
        # 戻すのはユーザー起点の新しいターン（stop_hook_active=false）だけ。
        save_state(state)
        sys.stderr.write(
            f"JEN_GATE: {MAX_CONSECUTIVE} 回連続で差し戻したが証拠が揃わない。"
            "ゲート未通過のまま終了したことを記録した（Human Gate）。\n")
        return 0

    state["consecutive_blocks"] = state.get("consecutive_blocks", 0) + 1
    save_state(state)
    reason = rewrite((proc.stderr or proc.stdout).strip()) or "JEN_GATE: 証拠台帳が全主張 MATCH ではない。"
    reason += (f"\n\n（Jen 完了ゲート: 差し戻し {state['consecutive_blocks']}/{MAX_CONSECUTIVE}。"
               "解けないなら、何ができて何で止まり人間は何をすべきかを報告して Human Gate にすること）")
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # アダプタの故障でセッションを壊さない（agentStop は fail-open）
        record({"event": "agentStop", "gated": False, "reason": f"adapter_error: {exc}"})
        raise SystemExit(0)
