#!/usr/bin/env python3
"""Jen for Copilot — 原文保全（userPromptSubmitted hook）.

Claude Code 版 Jen では、メインセッション（LLM）が「ユーザー入力を一字一句そのまま
`.jen/inbox.md` へ追記する」役を担っていた（relay-protocol.md）。
これは **LLM にお願いしている文** であり、v4 自身が弱いと分類している形である。

Copilot の `userPromptSubmitted` hook はプロンプト本文（`prompt`）を受け取れるので、
**原文の保全をハーネス側（決定論）へ移す**。LLM は保全に関与しないので、
要約・言い換え・省略が構造的に起きない。

## opt-in 条件

hook はリポジトリ内の全セッションで発火する。Jen と無関係な会話まで保存しないよう、
**`.jen/` ディレクトリが存在するときだけ**追記する（Stop ゲートの「台帳の存在が
opt-in」と同じ考え方）。`.jen/` を作るのは jen スキル / jen-pmo の初期化手順。

## 正直な限界

- cloud agent ではこの hook は**ジョブの最初の1回だけ**発火する（以後のユーザー入力が無い）。
  PR コメントでの追加指示は hook を通らないので、jen-pmo が手で追記する（従来どおり弱い経路）。
- VS Code の Local ハーネスではペイロード形式が異なり、本スクリプトは検証していない。

出力は返さない（userPromptSubmitted の command hook 出力は無視される）。
標準ライブラリのみ。
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

JEN = Path(".jen")
INBOX = JEN / "inbox.md"
HEADER = ("# Jen Inbox — ユーザー入力の原文（追記専用）\n\n"
          "userPromptSubmitted hook が**一字一句そのまま**追記する（Copilot 版）。\n"
          "誰も既存エントリを編集しない。jen-pmo と全 worker はここを「指示の正」として読む。\n")


def main() -> int:
    if not JEN.is_dir():
        return 0
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        return 0
    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return 0

    existing = INBOX.read_text(encoding="utf-8") if INBOX.is_file() else HEADER
    nums = [int(n) for n in re.findall(r"^## \[IN-(\d+)\]", existing, flags=re.M)]
    nxt = (max(nums) + 1) if nums else 1
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sep = "" if existing.endswith("\n") else "\n"
    # 原文は加工しない。末尾の改行だけ揃える。
    entry = f"{sep}\n## [IN-{nxt:03d}] {ts}  (captured by hook)\n{prompt.rstrip(chr(10))}\n"
    fresh = not INBOX.is_file() or INBOX.stat().st_size == 0
    with INBOX.open("a", encoding="utf-8") as fh:
        if fresh:
            fh.write(HEADER)
        fh.write(entry)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        raise SystemExit(0)
