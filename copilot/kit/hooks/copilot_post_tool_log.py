#!/usr/bin/env python3
"""Jen for Copilot — ツール呼び出しの実ログ（postToolUse hook）.

Claude 版 `post_tool_log.py` と同じ形式（`{"ts","event":"PostToolUse","data"}`）で
`.jen/logs/tool-events.jsonl` に追記する。`evidence_ledger.py budget` の委譲回数カウントと
行動監査（jen-audit）はこの形式を読む。

## Claude 版との違い（2点・どちらも意図的）

1. **`.jen/` が無いリポジトリでは何もしない。**
   Claude 版はプラグインとして有効なセッションでだけ動くが、Copilot の
   `.github/hooks/*.json` は**そのリポジトリの全セッション**で発火する。
   無条件に `.jen/logs/` を作ると、Jen を使っていない会話まで記録し、さらに
   `copilot_inbox_capture.py` の opt-in 条件（`.jen/` の存在）を勝手に満たしてしまう。
2. **ツール結果の本文を切り詰める。**
   `toolResult.textResultForLlm` はファイル内容やコマンド出力をそのまま含み、
   secret がログに載る経路になる。監査に要るのはツール名と引数なので、本文は
   先頭 `RESULT_LIMIT` 文字までにする。引数（`toolArgs`）は監査の材料なので残す
   ——`.jen/` を gitignore することは README で求めている。

委譲回数: Copilot のランタイムでは委譲ツールの名前が `task` なので、
`evidence_ledger.count_delegations()`（`agent`/`task` を数える）がそのまま使える。

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

JEN = Path(".jen")
RESULT_LIMIT = 2000


def main() -> int:
    if not JEN.is_dir():
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception as exc:
        data = {"parse_error": str(exc)}
    res = data.get("toolResult") if isinstance(data, dict) else None
    if isinstance(res, dict) and isinstance(res.get("textResultForLlm"), str):
        text = res["textResultForLlm"]
        if len(text) > RESULT_LIMIT:
            res["textResultForLlm"] = text[:RESULT_LIMIT] + f"…[truncated {len(text) - RESULT_LIMIT} chars]"
    logs = JEN / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "event": "PostToolUse", "surface": "copilot", "data": data}
    with (logs / "tool-events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        raise SystemExit(0)
