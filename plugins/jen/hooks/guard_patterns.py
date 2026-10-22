#!/usr/bin/env python3
"""Jen v4 — 危険コマンドの拒否パターン（単一の正）.

`pre_tool_guard.py`（PreToolUse hook）と `evidence_ledger.py`（run サブコマンド）の
両方がここを使う。evidence_ledger は証拠を得るために**自分で** subprocess を起動する。
パターンをここに集約しないと、`evidence_ledger.py run --cmd "rm -rf /"` が
PreToolUse を迂回する抜け道になる。

## この部品が前提している「モデルの不足」（P9）

モデルは破壊的・不可逆な操作を実行しようとすることがある。

**この前提はモデルの改善では解除しない。** 人間の承認が要るのは能力の問題ではなく
権限の問題であり、モデルがどれだけ賢くなっても「本番 deploy を人間に確認する」は
必要なままである。したがってこの部品は P9 の例外として扱う（期限が無い賭け）。

標準ライブラリのみ。
"""

from __future__ import annotations

import re

# (正規表現, 拒否理由). 判定は小文字化した文字列に対して行う。
PATTERNS: list[tuple[str, str]] = [
    (r"\brm\s+-rf\s+/(\s|$)", "rm -rf / is forbidden"),
    (r"\brm\s+-rf\s+\.\.(/|\s|$)", "rm -rf outside repository is forbidden"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard requires human approval"),
    # --force / --force-with-lease / 短縮形 -f（-f が単独オプションの場合）
    (r"\bgit\s+push\b.*(\s--force|\s-f(\s|$)|\s-[a-z]*f[a-z]*(\s|$))",
     "force push requires human approval"),
    (r"\bgit\s+push\b.*\s\+[a-z0-9._/-]+:", "force push via +refspec requires human approval"),
    (r"\b(npm|pnpm|yarn)\s+publish\b", "package publish requires human approval"),
    (r"\b(vercel|netlify|firebase|supabase)\s+deploy\b", "deployment requires human approval"),
    (r"\b(drop|truncate)\s+table\b", "destructive database operation requires human approval"),
    (r"\bchmod\s+-r\s+777\b", "recursive chmod 777 is forbidden"),
]

# 証拠台帳そのものを守るパターン。台帳を直接書き換えられると、
# ゲートは「偽造された証拠」を根拠に通ってしまう（コキエ 2026-03 の実験と同じ構図）。
# 台帳の更新は evidence_ledger.py 経由だけに限る。
LEDGER_PATTERNS: list[tuple[str, str]] = [
    (r">\s*\.jen/claims\.json", "write the claim ledger via evidence_ledger.py, not shell redirection"),
    (r">>\s*\.jen/claims\.json", "append to the claim ledger via evidence_ledger.py, not shell redirection"),
    (r"\b(sed|awk|perl|python3?)\b[^|;&]*-i[^|;&]*\.jen/claims\.json",
     "in-place edit of the claim ledger is forbidden; use evidence_ledger.py"),
    (r"\b(tee|cp|mv|install)\b[^|;&]*\.jen/claims\.json",
     "overwriting the claim ledger is forbidden; use evidence_ledger.py"),
    (r"\brm\b[^|;&]*\.jen/claims\.json", "deleting the claim ledger requires human approval"),
]


def deny_reason(command: str, *, include_ledger: bool = True) -> str | None:
    """`command` が拒否対象なら理由を返す。該当しなければ None。

    include_ledger=False は evidence_ledger.py 自身が呼ぶとき用
    （台帳を書くのは台帳スクリプトの正当な仕事なので、そこだけ除外する）。
    """
    if not command:
        return None
    low = command.lower()
    rules = PATTERNS + LEDGER_PATTERNS if include_ledger else PATTERNS
    for pattern, reason in rules:
        if re.search(pattern, low):
            return reason
    return None
