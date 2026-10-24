#!/usr/bin/env python3
"""AXIOM-0 とプラグイン構成の機械チェック.

`references/axiom-0.md` は「Claude のみで完結する」を最上位の制約に置いている。
だがドキュメントに書くだけなら、それは Jen 自身が v4 で否定している形
——**モデルにお願いしている文**——と同じである。だから機械で確認する。

確認項目:
  1. `plugins/*/hooks/*.py` の import が標準ライブラリ（＋同ディレクトリ）だけか
  2. hooks が外部コマンドを**必須**として呼んでいないか（任意なら違反ではない）
  3. `plugin.json` / `marketplace.json` が妥当な JSON で、版が一致しているか
  4. `plugin.json` が参照する hook ファイルが実在するか
  5. 両エディションの hooks が同一か（**意図的に同一**。片方だけ直す事故を防ぐ）
  6. Copilot 版（`copilot/`）のインストーラとアダプタも標準ライブラリのみか

標準ライブラリのみ。`python3 tests/check_axiom0.py` で単体でも走る。
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITIONS = ("jen", "jen-classic")
# hooks が居るディレクトリに置いてあるローカルモジュール
LOCAL_MODULES = {"guard_patterns"}
# 「あれば使う」が許される外部コマンド。必須にしているなら違反。
OPTIONAL_TOOLS_OK = True

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def hook_sources() -> list[Path]:
    files: list[Path] = []
    for ed in EDITIONS:
        files += sorted((ROOT / "plugins" / ed / "hooks").glob("*.py"))
    # Copilot 版: 対象リポジトリへ配るアダプタと、それを配るインストーラ
    files += sorted((ROOT / "copilot").glob("*.py"))
    files += sorted((ROOT / "copilot" / "kit" / "hooks").glob("*.py"))
    return files


def check_imports() -> None:
    std = set(sys.stdlib_module_names)
    for p in hook_sources():
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            fail(f"{p.relative_to(ROOT)}: 構文エラー: {exc}")
            continue
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mods = [node.module.split(".")[0]]
            for m in mods:
                if m == "__future__" or m in std or m in LOCAL_MODULES:
                    continue
                fail(f"{p.relative_to(ROOT)}: 標準ライブラリ外の import `{m}` "
                     f"— AXIOM-0 違反（hooks 本体は stdlib のみ）")


def check_no_mandatory_external_tools() -> None:
    """hooks が外部コマンドを必須にしていないか.

    `subprocess` で何かを呼ぶのは許される（evidence_ledger の run は
    ユーザーが渡したコマンドを実行するのが仕事）。禁じるのは
    「このコマンドが無いと hook 自体が動かない」形。
    ここでは、import 時や起動時に固定の外部コマンドを前提にしていないかを見る。
    """
    banned_literals = ("pdftotext", "yt-dlp", "tesseract", "jq", "npm ", "node ")
    for ed in EDITIONS:
        for p in sorted((ROOT / "plugins" / ed / "hooks").glob("*.py")):
            src = p.read_text(encoding="utf-8")
            for lit in banned_literals:
                # 拒否パターンの正規表現内の npm は正当（publish をブロックするため）
                if lit.strip() in ("npm", "node") and "guard_patterns" in p.name:
                    continue
                if f'"{lit}' in src or f"'{lit}" in src:
                    fail(f"{p.relative_to(ROOT)}: 固定の外部コマンド {lit!r} に依存している疑い "
                         f"— AXIOM-0 の運用原則（特定の道具を必須にしない）に反する")


def check_manifests() -> None:
    versions: dict[str, str] = {}
    mp = ROOT / ".claude-plugin" / "marketplace.json"
    try:
        market = json.loads(mp.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{mp.relative_to(ROOT)}: 妥当な JSON でない: {exc}")
        return
    versions["marketplace.metadata"] = market.get("metadata", {}).get("version", "?")
    for entry in market.get("plugins", []):
        versions[f"marketplace.{entry.get('name')}"] = entry.get("version", "?")

    for ed in EDITIONS:
        pj = ROOT / "plugins" / ed / ".claude-plugin" / "plugin.json"
        try:
            doc = json.loads(pj.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"{pj.relative_to(ROOT)}: 妥当な JSON でない: {exc}")
            continue
        versions[f"plugin.{ed}"] = doc.get("version", "?")
        # 4. hook ファイルの実在
        for event, groups in (doc.get("hooks") or {}).items():
            for group in groups:
                for hook in group.get("hooks", []):
                    cmd = hook.get("command", "")
                    if "${CLAUDE_PLUGIN_ROOT}/" not in cmd:
                        continue
                    rel = cmd.split("${CLAUDE_PLUGIN_ROOT}/", 1)[1].split()[0]
                    target = ROOT / "plugins" / ed / rel
                    if not target.is_file():
                        fail(f"{pj.relative_to(ROOT)}: {event} が参照する "
                             f"{rel} が実在しない")
    uniq = set(versions.values())
    if len(uniq) != 1:
        fail("版が一致していない: " + ", ".join(f"{k}={v}" for k, v in sorted(versions.items())))
    else:
        notes.append(f"版は全て一致: {uniq.pop()}")


def check_editions_share_hooks() -> None:
    """hooks は両版で同一であるべき（意図的）.

    v3.8.2 で「分岐すべき longrun スキルが同一だった」バグを見つけた。
    hooks は逆で、同一が正しい。片方だけ直す事故を防ぐためにここで固定する。
    """
    base = ROOT / "plugins" / "jen" / "hooks"
    other = ROOT / "plugins" / "jen-classic" / "hooks"
    names = {p.name for p in base.glob("*.py")} | {p.name for p in other.glob("*.py")}
    for name in sorted(names):
        a, b = base / name, other / name
        if not a.is_file():
            fail(f"hooks/{name} が jen に無い（jen-classic にはある）")
        elif not b.is_file():
            fail(f"hooks/{name} が jen-classic に無い（jen にはある）")
        elif a.read_bytes() != b.read_bytes():
            fail(f"hooks/{name} が両版で異なる — hooks は同一であるべき"
                 f"（片方だけ直した事故の可能性）")
    notes.append(f"hooks {len(names)} ファイルが両版で同一")


def main() -> int:
    check_imports()
    check_no_mandatory_external_tools()
    check_manifests()
    check_editions_share_hooks()

    for n in notes:
        print(f"ok   {n}")
    if failures:
        print()
        for f in failures:
            print(f"FAIL {f}", file=sys.stderr)
        print(f"\n{len(failures)} 件の違反", file=sys.stderr)
        return 1
    print("ok   AXIOM-0 準拠")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
