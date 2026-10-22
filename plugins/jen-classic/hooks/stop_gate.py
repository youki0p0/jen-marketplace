#!/usr/bin/env python3
"""Jen v4 — 完了ゲート（Stop hook）.

セッションが終わろうとするとき、証拠台帳（`.jen/claims.json`）の被覆を見て
**全主張が MATCH でなければ完了を認めない**（exit 2 で差し戻す）。

判断は決定論。LLM に「終わっていいか」を聞かない。
出典は `evidence_ledger.py` の docstring（HALT / Jain / Anthropic / コキエ）。

## 台帳が無いセッションをどう扱うか（設計上の妥協・明示する）

プラグインは全セッションで有効になるので、台帳が無いだけで停止を塞ぐと
普通の会話すら終われなくなる。したがって **台帳の存在がゲートの opt-in** とする。

ただし「台帳を作らなければゲートを回避できる」という穴が残る。これを塞ぐ代わりに、
**ゲート無しで終わったことを必ず記録する**（`.jen/logs/stop-events.jsonl` の
`gated: false`）。行動監査（`/jen:jen-audit`）がこれを拾えるので、
「主張を宣言せずに完了した回数」は事後に数えられる。
穴を黙って残すのではなく、見えるようにしてから残している。

## この部品が前提している「モデルの不足」（P9）

モデルは**早すぎる完了宣言**をする。Anthropic も同じ失敗を観測している
（「a later agent instance would look around, see that progress had been made,
and declare [the project complete]」/ effective-harnesses-for-long-running-agents）。
MAST(2503.13657) の14失敗モードにも「早すぎる終了」「検証しない」が入っている。

この前提が外れたら（モデルが被覆を正しく自己申告するようになったら）、
`sensor_mode: final_gate` のまま最終1回だけにし、最後は hooks から外してよい。

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

LEDGER = Path(".jen/claims.json")
LOG = Path(".jen/logs/stop-events.jsonl")
LEDGER_SCRIPT = Path(__file__).resolve().parent / "evidence_ledger.py"


def record(entry: dict) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        entry["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 記録に失敗してもセッションは壊さない


def main() -> int:
    try:
        json.load(sys.stdin)
    except Exception:
        pass  # ペイロードは使わない。読み捨てて続ける

    if not LEDGER.exists():
        # 主張が宣言されていないミッション。塞がないが、必ず記録する（上の注記参照）。
        record({"event": "Stop", "gated": False, "reason": "no_ledger"})
        return 0

    try:
        doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"JEN_GATE: 台帳を読めない（{exc}）。人間の確認が必要。", file=sys.stderr)
        record({"event": "Stop", "gated": False, "reason": "ledger_unreadable"})
        return 2

    if doc.get("gate") == "off":
        # 人間が明示的に切った場合のみ。Jen の Human Gate 思想どおり
        # 逃げ道は用意するが、切ったことを記録に残す。
        record({"event": "Stop", "gated": False, "reason": "gate_off_by_human"})
        print("JEN_GATE: 人間により無効化されている（記録済み）", file=sys.stderr)
        return 0

    if not LEDGER_SCRIPT.is_file():
        print(f"JEN_GATE: {LEDGER_SCRIPT} が無い。判定できないので人間の確認が必要。",
              file=sys.stderr)
        record({"event": "Stop", "gated": False, "reason": "ledger_script_missing"})
        return 2

    proc = subprocess.run([sys.executable, str(LEDGER_SCRIPT), "gate"],
                          capture_output=True, text=True, check=False)
    passed = proc.returncode == 0
    record({"event": "Stop", "gated": True, "passed": passed,
            "mission_rev": doc.get("mission_rev"), "tier": doc.get("tier"),
            "sensor_mode": doc.get("sensor_mode"),
            "claims": {cid: c.get("state") for cid, c in doc.get("claims", {}).items()}})

    if passed:
        sys.stderr.write(proc.stdout)
        return 0

    # 差し戻す。何が足りないかと、次に何をすればよいかを必ず出す
    # （v3.4 の「停止するときは3点報告」の不変条件を踏襲）。
    sys.stderr.write(proc.stderr or proc.stdout)
    sys.stderr.write(
        "\n--- 完了を認めない。次のどれかをする ---\n"
        "1. 未被覆の主張に強い証拠を付ける:\n"
        "   python3 ${CLAUDE_PLUGIN_ROOT}/hooks/evidence_ledger.py run "
        "--claim <ID> --cmd '<検証コマンド>'\n"
        "2. 主張そのものが間違っていた場合は、人間に確認してから版を切る:\n"
        "   python3 ${CLAUDE_PLUGIN_ROOT}/hooks/evidence_ledger.py revise --note '<理由>'\n"
        "3. 解けない場合は Human Gate として、何ができて何で止まったかを報告する。\n"
        "   ゲート自体を切るのは人間の判断（.jen/claims.json の \"gate\": \"off\"）。\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
