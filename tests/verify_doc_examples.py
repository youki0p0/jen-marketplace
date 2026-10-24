#!/usr/bin/env python3
"""ドキュメントに書いたコマンド例を、実際に実行して検証する.

`# VERIFY-BLOCK` で始まる bash のコードブロックを抜き出し、
**空の一時ディレクトリで実際に走らせる**。1つでも失敗したら exit 1。

なぜこれが要るか: v4 の主張は「エージェントがトークン出力では作れない証拠を持つ」である。
ドキュメントに書いたコマンドが実際に動くかを**誰も確かめないなら**、
「動きます」という記述はエージェントの自己申告——v4 自身が weak と分類する証拠——にすぎない。
実行して初めて strong になる。

使い方:
    python3 tests/verify_doc_examples.py docs/jen-v4-usage.md

標準ライブラリのみ。
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "plugins" / "jen" / "hooks"
MARKER = "# VERIFY-BLOCK"
FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)


def blocks(md: Path) -> list[str]:
    text = md.read_text(encoding="utf-8")
    return [b for b in FENCE.findall(text) if MARKER in b]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <markdown file>", file=sys.stderr)
        return 2
    md = Path(argv[1])
    if not md.is_file():
        print(f"ファイルが無い: {md}", file=sys.stderr)
        return 2
    if not HOOKS.is_dir():
        print(f"hooks が無い: {HOOKS}", file=sys.stderr)
        return 2

    found = blocks(md)
    if not found:
        print(f"FAIL {md}: `{MARKER}` を含む bash ブロックが1つも無い", file=sys.stderr)
        return 1

    failures = 0
    for i, block in enumerate(found, 1):
        work = Path(tempfile.mkdtemp(prefix="docverify-"))
        try:
            script = work / "block.sh"
            script.write_text(block, encoding="utf-8")
            proc = subprocess.run(
                ["bash", str(script)], cwd=work, capture_output=True, text=True,
                env={"PATH": "/usr/bin:/bin:/usr/local/bin", "H": str(HOOKS),
                     "HOME": str(work), "LANG": "C.UTF-8"},
                timeout=300, check=False)
            if proc.returncode == 0:
                print(f"ok   ブロック{i}: 書いてあるとおりに動いた（{len(block.splitlines())}行）")
            else:
                failures += 1
                print(f"FAIL ブロック{i}: exit={proc.returncode}", file=sys.stderr)
                print("--- stdout ---\n" + proc.stdout, file=sys.stderr)
                print("--- stderr ---\n" + proc.stderr, file=sys.stderr)
        except subprocess.TimeoutExpired:
            failures += 1
            print(f"FAIL ブロック{i}: タイムアウト", file=sys.stderr)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    if failures:
        print(f"\n{failures}/{len(found)} ブロックが失敗", file=sys.stderr)
        return 1
    print(f"ok   {md}: {len(found)} ブロックすべて実行できた")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
