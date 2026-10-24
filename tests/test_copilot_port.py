#!/usr/bin/env python3
"""Jen for GitHub Copilot（copilot/）の試験. 標準ライブラリのみ.

守っている性質:
  1. 全エディション×全 surface で変換が通り、Copilot の制約を満たす
     （agent 本文 ≤30,000 文字 / skill 名は小文字ハイフン・ディレクトリ名と一致 /
      description ≤1024 / tools は Copilot の別名だけ / jen-pmo だけがピッカーに出る）
  2. 判断する知能は Claude のみ（AXIOM-0）: 展開されたモデルは全て Claude 系
  3. hooks 定義が Copilot のスキーマ（version:1・既知イベント・command 型）で、参照先が実在する
  4. 完了ゲート: 未被覆なら {"decision":"block"} を出す（exit 2 では Copilot は止まらない）
  5. 完了ゲート: 連続 block は上限で諦め、block_cap を記録する（CLI の 8 回上限より手前）
  6. 完了ゲート: 全被覆なら何も出さない（＝完了を許す）
  7. ガード: 危険コマンドを permissionDecision:deny で拒否する
  8. ガード: 編集ツールでの台帳書き換えを拒否し、台帳に言及するだけの編集は通す
  9. ガード: 内部故障では「判断なし」を返す（fail-closed で全ツールを止めない）
 10. `.jen/` が無いリポジトリでは、どの hook も何も書かない（opt-in）
 11. 原文保全: プロンプトを逐語で連番追記する
 12. 手で変更されたファイルは --force なしに上書きしない／アンインストールでも残す
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "copilot" / "install.py"
TOOL_ALIASES = {"read", "edit", "execute", "search", "agent", "web", "todo"}
HOOK_EVENTS = {"sessionStart", "sessionEnd", "userPromptSubmitted", "userPromptTransformed",
               "preToolUse", "postToolUse", "postToolUseFailure", "agentStop", "subagentStart",
               "subagentStop", "errorOccurred", "preCompact", "permissionRequest", "notification"}


def install(target: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(INSTALL), "--target", str(target), *args],
                          capture_output=True, text=True, check=False)


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    end = text.index("\n---\n", 4)
    meta = {}
    for line in text[4:end].splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = json.loads(v.strip())  # install.py は値を JSON 表記で出す
    return meta, text[end + 5:]


def hook(target: Path, name: str, payload, cwd: Path | None = None) -> subprocess.CompletedProcess:
    raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return subprocess.run([sys.executable, str(target / ".github/hooks/jen" / name)],
                          input=raw, cwd=cwd or target, capture_output=True, text=True, check=False)


class ConversionTest(unittest.TestCase):
    def test_all_variants_satisfy_copilot_limits(self) -> None:
        for edition in ("jen", "jen-classic"):
            for surface in ("portable", "cli", "vscode"):
                for fable in ((), ("--fable",)):
                    with self.subTest(edition=edition, surface=surface, fable=bool(fable)), \
                            tempfile.TemporaryDirectory() as tmp:
                        t = Path(tmp)
                        res = install(t, "--edition", edition, "--surface", surface, *fable)
                        self.assertEqual(res.returncode, 0, res.stderr)
                        self._check_agents(t, surface)
                        self._check_skills(t)
                        self._check_hooks(t)

    def _check_agents(self, t: Path, surface: str) -> None:
        agents = sorted((t / ".github/agents").glob("*.agent.md"))
        self.assertEqual(len(agents), 18)
        invocable = []
        for p in agents:
            meta, body = frontmatter(p)
            self.assertTrue(meta.get("description"), p.name)
            self.assertLessEqual(len(body), 30_000, p.name)
            self.assertTrue(set(meta["tools"]) <= TOOL_ALIASES, (p.name, meta["tools"]))
            self.assertNotIn("$CLAUDE_PLUGIN_ROOT/hooks", body, p.name)
            models = meta["model"] if isinstance(meta["model"], list) else [meta["model"]]
            models += meta.get("models", [])
            for m in models:  # AXIOM-0: 判断する知能は Claude のみ
                self.assertTrue(m.lower().startswith("claude"), (p.name, m))
            if surface == "cli":
                self.assertEqual(meta.get("modelPolicy"), "required", p.name)
            if meta["user-invocable"]:
                invocable.append(meta["name"])
            if "agent" in meta["tools"]:
                self.assertEqual(meta["name"], "jen-pmo", "委譲できるのは jen-pmo だけ")
        self.assertEqual(invocable, ["jen-pmo"])

    def _check_skills(self, t: Path) -> None:
        names = set()
        for p in (t / ".github/skills").glob("*/SKILL.md"):
            meta, _ = frontmatter(p)
            self.assertEqual(meta["name"], p.parent.name)
            self.assertRegex(meta["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
            self.assertLessEqual(len(meta["description"]), 1024)
            names.add(meta["name"])
        self.assertTrue({"jen", "jen-review", "jen-repair", "jen-release", "jen-longrun",
                         "jen-status", "jen-board", "jen-standup", "jen-pr", "jen-audit"} <= names)
        self.assertTrue((t / ".github/skills/jen/references/copilot-delta.md").is_file())

    def _check_hooks(self, t: Path) -> None:
        doc = json.loads((t / ".github/hooks/jen.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["version"], 1)
        for event, entries in doc["hooks"].items():
            self.assertIn(event, HOOK_EVENTS)
            for e in entries:
                self.assertEqual(e.get("type", "command"), "command")
                self.assertIn("bash", e)  # cloud agent は bash / command しか見ない
                script = re.search(r"(\.github/hooks/jen/\S+\.py)", e["bash"]).group(1)
                self.assertTrue((t / script).is_file(), script)
        # 完了ゲートは agentStop にだけ登録する（worker の完了はミッションの完了ではない）
        self.assertNotIn("subagentStop", doc["hooks"])
        self.assertIn("agentStop", doc["hooks"])


class HookTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.t = Path(self._tmp.name)
        res = install(self.t)
        self.assertEqual(res.returncode, 0, res.stderr)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def ledger(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(self.t / ".github/hooks/jen/evidence_ledger.py"), *args],
                              cwd=self.t, capture_output=True, text=True, check=False)

    def test_no_jen_dir_means_no_writes(self) -> None:
        hook(self.t, "copilot_inbox_capture.py", {"prompt": "hi"})
        hook(self.t, "copilot_post_tool_log.py", {"toolName": "view", "toolArgs": {}})
        r = hook(self.t, "copilot_stop_gate.py", {"stop_hook_active": False})
        self.assertEqual(r.stdout, "")
        self.assertFalse((self.t / ".jen").exists())

    def test_stop_gate_blocks_with_json_then_caps(self) -> None:
        self.assertEqual(self.ledger("init", "--tier", "sonnet", "--claim", "C1=tests pass").returncode, 0)
        r = hook(self.t, "copilot_stop_gate.py", {"stop_hook_active": False})
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn(".github/hooks/jen/evidence_ledger.py", out["reason"])
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", out["reason"])
        blocks = 1
        while True:
            r = hook(self.t, "copilot_stop_gate.py", {"stop_hook_active": True})
            if not r.stdout:
                break
            blocks += 1
            self.assertLess(blocks, 8, "CLI の runaway guard（8回）より手前で諦めること")
        log = (self.t / ".jen/logs/stop-events.jsonl").read_text(encoding="utf-8")
        self.assertIn('"block_cap"', log)
        # 強制継続が続く限り再び block しない
        self.assertEqual(hook(self.t, "copilot_stop_gate.py", {"stop_hook_active": True}).stdout, "")
        # ユーザー起点の新しいターンでは再び差し戻す
        self.assertIn("block", hook(self.t, "copilot_stop_gate.py", {"stop_hook_active": False}).stdout)

    def test_stop_gate_allows_when_covered(self) -> None:
        self.ledger("init", "--tier", "sonnet", "--claim", "C1=ok")
        self.assertEqual(self.ledger("run", "--claim", "C1", "--cmd", f"{sys.executable} -c pass").returncode, 0)
        r = hook(self.t, "copilot_stop_gate.py", {"stop_hook_active": False})
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def deny(self, payload) -> bool:
        r = hook(self.t, "copilot_pre_tool_guard.py", payload)
        self.assertEqual(r.returncode, 0, r.stderr)
        return bool(r.stdout.strip()) and json.loads(r.stdout).get("permissionDecision") == "deny"

    def test_guard_shell(self) -> None:
        self.assertTrue(self.deny({"toolName": "bash", "toolArgs": {"command": "git push -f origin main"}}))
        self.assertTrue(self.deny({"toolName": "bash", "toolArgs": json.dumps({"command": "vercel deploy"})}))
        self.assertTrue(self.deny({"toolName": "powershell", "toolArgs": {"command": "echo {} > .jen/claims.json"}}))
        self.assertFalse(self.deny({"toolName": "bash", "toolArgs": {"command": "npm test"}}))

    def test_guard_edit_tools_protect_ledger(self) -> None:
        self.assertTrue(self.deny({"toolName": "create", "toolArgs": {"path": ".jen/claims.json"}}))
        self.assertTrue(self.deny({"toolName": "edit", "toolArgs": {"path": "/repo/.jen/claims.json"}}))
        patch = "*** Begin Patch\n*** Update File: .jen/claims.json\n@@\n-a\n+b\n*** End Patch"
        self.assertTrue(self.deny({"toolName": "apply_patch", "toolArgs": {"input": patch}}))
        self.assertFalse(self.deny({"toolName": "edit",
                                    "toolArgs": {"path": "README.md", "new_str": "see .jen/claims.json"}}))

    def test_guard_internal_failure_is_no_decision(self) -> None:
        (self.t / ".github/hooks/jen/guard_patterns.py").write_text("raise RuntimeError('boom')\n")
        r = hook(self.t, "copilot_pre_tool_guard.py", {"toolName": "bash", "toolArgs": {"command": "ls"}})
        self.assertEqual((r.returncode, r.stdout), (0, "{}"))
        self.assertFalse(self.deny("not json"))

    def test_inbox_capture_is_verbatim(self) -> None:
        (self.t / ".jen").mkdir()
        original = "ログイン画面を直して。\n  誤字もそのまま　です\n\n- 箇条書きも"
        hook(self.t, "copilot_inbox_capture.py", {"prompt": original})
        hook(self.t, "copilot_inbox_capture.py", {"prompt": "二通目"})
        inbox = (self.t / ".jen/inbox.md").read_text(encoding="utf-8")
        self.assertIn(original, inbox)
        self.assertRegex(inbox, r"## \[IN-001\].*\n" + re.escape(original))
        self.assertRegex(inbox, r"## \[IN-002\].*\n二通目")

    def test_delegations_counted_from_copilot_logs(self) -> None:
        (self.t / ".jen").mkdir()
        hook(self.t, "copilot_post_tool_log.py",
             {"toolName": "task", "toolArgs": {}, "toolResult": {"textResultForLlm": "x" * 5000}})
        hook(self.t, "copilot_post_tool_log.py", {"toolName": "view", "toolArgs": {}})
        self.ledger("init", "--tier", "sonnet", "--claim", "C1=x")
        self.assertIn("委譲回数: 1", self.ledger("budget").stdout)
        line = (self.t / ".jen/logs/tool-events.jsonl").read_text(encoding="utf-8").splitlines()[0]
        self.assertLess(len(line), 3000, "ツール結果の本文は切り詰める")


class LifecycleTest(unittest.TestCase):
    def test_manual_edits_are_respected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            self.assertEqual(install(t).returncode, 0)
            edited = t / ".github/skills/jen-pr/SKILL.md"
            edited.write_text(edited.read_text(encoding="utf-8") + "\nmine\n", encoding="utf-8")
            self.assertEqual(install(t).returncode, 1, "手で変更されたファイルを黙って上書きしない")
            self.assertEqual(install(t, "--surface", "vscode", "--force").returncode, 0)
            edited.write_text("mine\n", encoding="utf-8")
            res = install(t, "--uninstall")
            self.assertEqual(res.returncode, 0)
            self.assertTrue(edited.is_file(), "手で変更されたファイルは残す")
            self.assertFalse((t / ".github/agents").exists())
            self.assertFalse((t / ".github/jen-copilot.lock.json").exists())

    def test_existing_foreign_file_is_a_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / ".github/hooks").mkdir(parents=True)
            (t / ".github/hooks/jen.json").write_text("{}")
            self.assertEqual(install(t).returncode, 1)
            self.assertEqual((t / ".github/hooks/jen.json").read_text(), "{}")


if __name__ == "__main__":
    unittest.main()
