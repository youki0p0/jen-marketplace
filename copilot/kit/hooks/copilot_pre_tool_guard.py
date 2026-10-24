#!/usr/bin/env python3
"""Jen for Copilot — 破壊的操作ガード（preToolUse hook アダプタ）.

拒否パターンは Claude 版と同じ `guard_patterns.py`（単一の正）を使う。
このファイルは Copilot の入出力形式への翻訳だけを担う。

## Claude 版との違い

1. **入力形式**: camelCase の `preToolUse` は `{toolName, toolArgs}` を渡す。
   ランタイムのツール名は `bash` / `powershell` / `create` / `edit` /
   `apply_patch` / `str_replace_editor` など（hooks-reference の対応表）。
   引数のキー名はツールごとに文書化されていないので、**既知のキーを順に探し、
   見つからなければ引数全体を文字列化して検査する**（取りこぼすより過検出を選ぶ）。
2. **ファイル編集ツールからの台帳書き換えも拒否する**: Claude 版はシェル経由の
   書き換えだけを塞いでいた（Write/Edit は PreToolUse の matcher が Bash のみ）。
   Copilot では編集ツールが `.jen/claims.json` を直接書けるので、ここで塞ぐ。
3. **出力**: `{"permissionDecision":"deny","permissionDecisionReason":...}` を1つだけ出す。
4. **故障時の扱い（意図的な妥協・明示する）**: Copilot の command 型 preToolUse は
   fail-closed で、スクリプトが落ちると**そのツール呼び出しが拒否される**。
   ガードのバグで全ツールが止まるのを避けるため、内部例外は捕まえて「判断なし」
   （`{}`）を返し、`.jen/logs/guard-errors.jsonl` に記録する。
   一方、**タイムアウトは Copilot 側で常に fail-open** なので、重い処理はしない。

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SHELL_TOOLS = {"bash", "powershell", "shell", "execute", "run_in_terminal", "terminal"}
EDIT_TOOLS = {"create", "edit", "write", "str_replace", "str_replace_editor",
              "apply_patch", "multiedit", "notebookedit", "insert"}
COMMAND_KEYS = ("command", "cmd", "script", "input", "commandLine")
PATH_KEYS = ("path", "file_path", "filePath", "filename", "target", "file")
LEDGER = ".jen/claims.json"


def log_error(msg: str) -> None:
    try:
        p = Path(".jen/logs/guard-errors.jsonl")
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 "error": msg}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def as_obj(args):
    if isinstance(args, str):
        try:
            return json.loads(args)
        except Exception:
            return args
    return args


def pick(args, keys) -> str:
    if isinstance(args, dict):
        for k in keys:
            v = args.get(k)
            if isinstance(v, str) and v:
                return v
    return ""


def deny(reason: str) -> int:
    sys.stdout.write(json.dumps({"permissionDecision": "deny",
                                 "permissionDecisionReason": f"JEN_GUARD_BLOCKED: {reason}"},
                                ensure_ascii=False))
    return 0


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 読めない入力には判断しない（Claude 版と同じ）

    from guard_patterns import deny_reason  # 読めなければ下の except で記録される

    tool = str(data.get("toolName") or data.get("tool_name") or "").lower()
    args = as_obj(data.get("toolArgs", data.get("tool_input")))
    flat = args if isinstance(args, str) else json.dumps(args, ensure_ascii=False)

    if tool in SHELL_TOOLS:
        cmd = pick(args, COMMAND_KEYS) or flat
        reason = deny_reason(cmd)
        if reason:
            return deny(f"{reason} / Command: {cmd}")
        return 0

    if tool in EDIT_TOOLS or any(k in tool for k in ("edit", "write", "patch", "create")):
        target = pick(args, PATH_KEYS).replace("\\", "/")
        # パッチ形式は本文ではなくヘッダ行（*** / --- / +++ / diff）だけを見る。
        # 本文に「.jen/claims.json」と書いてあるだけの文書編集まで止めないため。
        patch = pick(args, ("patch", "input", "diff")) or (args if isinstance(args, str) else "")
        header_hit = any(line.lstrip().startswith(("***", "---", "+++", "diff"))
                         and LEDGER in line.replace("\\", "/")
                         for line in patch.splitlines())
        if target.endswith(LEDGER) or header_hit:
            return deny("証拠台帳 .jen/claims.json は .github/hooks/jen/evidence_ledger.py "
                        "経由でのみ更新できる（直接編集はゲートの偽造経路になる）")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        log_error(f"{type(exc).__name__}: {exc}")
        sys.stdout.write("{}")
        raise SystemExit(0)
