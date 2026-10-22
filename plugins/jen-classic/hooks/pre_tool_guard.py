#!/usr/bin/env python3
"""Jen — 破壊的操作のガード（PreToolUse hook）.

拒否パターンは `guard_patterns.py` に集約してある（単一の正）。
`evidence_ledger.py` の run サブコマンドも同じモジュールを使う —
分けると台帳経由で PreToolUse を迂回する穴になる。

v4 で追加: 証拠台帳（`.jen/claims.json`）そのものの書き換えを拒否する。
台帳を直接書ければ、完了ゲートは偽造された証拠を根拠に通ってしまう。

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from guard_patterns import deny_reason
except Exception as exc:  # ガードを読めないなら、黙って通さない
    print(f"JEN_GUARD_ERROR: guard_patterns.py を読めない: {exc}", file=sys.stderr)
    raise SystemExit(0)

try:
    data = json.load(sys.stdin)
except Exception:
    raise SystemExit(0)

tool = (data.get("tool_name") or data.get("tool") or "").lower()
cmd = ""
if isinstance(data.get("tool_input"), dict):
    cmd = data["tool_input"].get("command") or data["tool_input"].get("cmd") or ""

if tool == "bash" or cmd:
    reason = deny_reason(cmd)
    if reason:
        print(f"JEN_GUARD_BLOCKED: {reason}\nCommand: {cmd}", file=sys.stderr)
        raise SystemExit(2)

raise SystemExit(0)
