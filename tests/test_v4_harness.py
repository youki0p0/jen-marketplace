#!/usr/bin/env python3
"""Jen v4 ハーネスの試験. 標準ライブラリのみ（`python3 -m unittest -v` で走る）.

守っている性質:
  1. 弱い証拠は MATCH に届かない（require=medium のとき）
  2. 強い証拠は MATCH に届く
  3. 失敗した実行は記録されるが状態を上げない
  4. 状態は単調非減少（下がらない）
  5. 台帳の改竄は封印の不一致で検出される
  6. ログの実体が無い「強い証拠」は捏造として検出される
  7. 危険コマンドは台帳の run 経由でも拒否される（PreToolUse 迂回の穴が無い）
  8. 台帳の直接書き換えは PreToolUse で拒否される
  9. revise は被覆をリセットする（Bates 1989・問いが変わったら引き継がない）
 10. Stop ゲートの終了コードが仕様どおり（未被覆=2 / 全被覆=0 / 台帳なし=0）
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "jen" / "hooks"
LEDGER = HOOKS / "evidence_ledger.py"
GATE = HOOKS / "stop_gate.py"
GUARD = HOOKS / "pre_tool_guard.py"


def run(args: list[str], cwd: Path, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=cwd, input=stdin,
                          capture_output=True, text=True, check=False)


def ledger(cwd: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
    return run([str(LEDGER), *args], cwd, stdin)


def read_doc(cwd: Path) -> dict:
    return json.loads((cwd / ".jen/claims.json").read_text(encoding="utf-8"))


def write_doc(cwd: Path, doc: dict, *, reseal: bool = False) -> None:
    if reseal:
        body = {k: v for k, v in doc.items() if k != "seal"}
        doc["seal"] = hashlib.sha256(json.dumps(
            body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    (cwd / ".jen/claims.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                                          encoding="utf-8")


class HarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self._tmp.name)
        res = ledger(self.cwd, "init", "--tier", "sonnet",
                     "--claim", "C1=テストが通る", "--claim", "C2=lint が通る")
        self.assertEqual(res.returncode, 0, res.stderr)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # 1
    def test_weak_evidence_stops_at_partial(self):
        ledger(self.cwd, "attest", "--claim", "C1", "--kind", "note", "--detail", "やったと報告")
        self.assertEqual(read_doc(self.cwd)["claims"]["C1"]["state"], "PARTIAL")

    # 2
    def test_strong_evidence_reaches_match(self):
        res = ledger(self.cwd, "run", "--claim", "C1", "--cmd", "true")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(read_doc(self.cwd)["claims"]["C1"]["state"], "MATCH")

    # 3
    def test_failed_run_is_recorded_but_does_not_raise_state(self):
        res = ledger(self.cwd, "run", "--claim", "C1", "--cmd", "false")
        self.assertEqual(res.returncode, 1)
        claim = read_doc(self.cwd)["claims"]["C1"]
        self.assertEqual(claim["state"], "NULL")
        self.assertEqual(len(claim["evidence"]), 1)
        self.assertFalse(claim["evidence"][0]["satisfied"])
        self.assertTrue((self.cwd / claim["evidence"][0]["log"]).is_file(),
                        "失敗したときのログが残っていない（最も価値のある記録）")

    def test_two_runs_in_same_second_keep_both_logs(self):
        ledger(self.cwd, "run", "--claim", "C1", "--cmd", "false")
        ledger(self.cwd, "run", "--claim", "C1", "--cmd", "true")
        logs = list((self.cwd / ".jen/logs/evidence").glob("C1-*.txt"))
        self.assertEqual(len(logs), 2, "同一秒の2回でログ名が衝突している")

    # 4
    def test_state_is_monotonic(self):
        ledger(self.cwd, "run", "--claim", "C1", "--cmd", "true")
        self.assertEqual(read_doc(self.cwd)["claims"]["C1"]["state"], "MATCH")
        ledger(self.cwd, "run", "--claim", "C1", "--cmd", "false")
        self.assertEqual(read_doc(self.cwd)["claims"]["C1"]["state"], "MATCH",
                         "失敗を足したら状態が下がった（単調性が壊れている）")

    # 5
    def test_tampering_breaks_the_seal(self):
        doc = read_doc(self.cwd)
        for claim in doc["claims"].values():
            claim["state"] = "MATCH"
        write_doc(self.cwd, doc)  # 封印を再計算しない
        res = ledger(self.cwd, "gate")
        self.assertEqual(res.returncode, 2)
        self.assertIn("封印が一致しない", res.stderr)
        self.assertIn("UNTRUSTED", res.stderr, "偽造された状態が MATCH のまま表示されている")

    # 6
    def test_orphan_strong_evidence_is_detected_even_when_resealed(self):
        doc = read_doc(self.cwd)
        for claim in doc["claims"].values():
            claim["state"] = "MATCH"
            claim["evidence"] = [{"strength": "strong", "kind": "command",
                                  "satisfied": True, "log": ".jen/logs/evidence/nope.txt"}]
        write_doc(self.cwd, doc, reseal=True)  # 封印まで再計算した攻撃
        res = ledger(self.cwd, "gate")
        self.assertEqual(res.returncode, 2, "封印を再計算されたら通ってしまった")
        self.assertIn("捏造の疑い", res.stderr)

    # 7
    def test_ledger_run_refuses_dangerous_commands(self):
        for cmd in ("git push --force origin main", "rm -rf / ", "npm publish"):
            res = ledger(self.cwd, "run", "--claim", "C1", "--cmd", cmd)
            self.assertEqual(res.returncode, 2, f"台帳経由で {cmd!r} が通った（迂回の穴）")
            self.assertIn("実行を拒否", res.stderr)

    # 8
    def test_guard_blocks_direct_ledger_writes(self):
        blocked = ['echo x > .jen/claims.json', 'sed -i "s/a/b/" .jen/claims.json',
                   'cp f .jen/claims.json', 'rm .jen/claims.json',
                   'tee .jen/claims.json < f']
        for cmd in blocked:
            payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
            res = run([str(GUARD)], self.cwd, payload)
            self.assertEqual(res.returncode, 2, f"{cmd!r} が通った")
        for cmd in ("cat .jen/claims.json", "ls -la", "git push origin main"):
            payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
            res = run([str(GUARD)], self.cwd, payload)
            self.assertEqual(res.returncode, 0, f"{cmd!r} が誤ってブロックされた")

    def test_guard_keeps_the_v3_pattern_set(self):
        """v3.7.2 で固めた9パターンの回帰."""
        for cmd in ("rm -rf /", "git push -f origin main", "git push origin +main:main",
                    "git reset --hard HEAD~1", "npm publish", "vercel deploy",
                    "DROP TABLE users", "chmod -R 777 .", "rm -rf ../x"):
            payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
            res = run([str(GUARD)], self.cwd, payload)
            self.assertEqual(res.returncode, 2, f"v3 のパターンが壊れた: {cmd!r}")

    # 9
    def test_revise_resets_coverage(self):
        ledger(self.cwd, "run", "--claim", "C1", "--cmd", "true")
        ledger(self.cwd, "run", "--claim", "C2", "--cmd", "true")
        self.assertEqual(ledger(self.cwd, "gate").returncode, 0)
        res = ledger(self.cwd, "revise", "--note", "受入条件が変わった")
        self.assertEqual(res.returncode, 0, res.stderr)
        doc = read_doc(self.cwd)
        self.assertEqual(doc["mission_rev"], 2)
        self.assertEqual(doc["claims"]["C1"]["state"], "NULL", "版を切ったのに被覆が残った")
        self.assertEqual(ledger(self.cwd, "gate").returncode, 2)

    # 10
    def test_stop_gate_exit_codes(self):
        payload = json.dumps({"session_id": "t"})
        self.assertEqual(run([str(GATE)], self.cwd, payload).returncode, 2,
                         "未被覆なのに完了が通った")
        ledger(self.cwd, "run", "--claim", "C1", "--cmd", "true")
        self.assertEqual(run([str(GATE)], self.cwd, payload).returncode, 2,
                         "部分被覆で完了が通った")
        ledger(self.cwd, "run", "--claim", "C2", "--cmd", "true")
        self.assertEqual(run([str(GATE)], self.cwd, payload).returncode, 0,
                         "全被覆なのに完了が塞がれた")

    def test_stop_gate_without_ledger_allows_but_records(self):
        empty = Path(tempfile.mkdtemp())
        try:
            payload = json.dumps({"session_id": "t"})
            self.assertEqual(run([str(GATE)], empty, payload).returncode, 0)
            line = json.loads((empty / ".jen/logs/stop-events.jsonl").read_text().strip())
            self.assertFalse(line["gated"])
            self.assertEqual(line["reason"], "no_ledger")
        finally:
            __import__("shutil").rmtree(empty, ignore_errors=True)

    def test_human_can_disable_the_gate_but_it_is_recorded(self):
        doc = read_doc(self.cwd)
        doc["gate"] = "off"
        write_doc(self.cwd, doc, reseal=True)
        payload = json.dumps({"session_id": "t"})
        self.assertEqual(run([str(GATE)], self.cwd, payload).returncode, 0)
        line = json.loads((self.cwd / ".jen/logs/stop-events.jsonl").read_text().strip())
        self.assertEqual(line["reason"], "gate_off_by_human")

    def test_strong_evidence_cannot_be_asserted_via_cli(self):
        """強い証拠を宣言する CLI 経路が無いこと（run だけが作れる）."""
        res = ledger(self.cwd, "attest", "--claim", "C1", "--kind", "strong", "--detail", "x")
        self.assertNotEqual(res.returncode, 0,
                            "attest から強い証拠を宣言できてしまった")

    # Lean 方針（jen-classic）の資源計測
    def test_budget_says_unknown_rather_than_zero_when_log_is_absent(self):
        """測れないときに黙って 0 と言わないこと（最も危険な嘘）."""
        res = ledger(self.cwd, "init", "--force", "--tier", "haiku",
                     "--max-delegations", "3", "--claim", "C1=x")
        self.assertEqual(res.returncode, 0, res.stderr)
        res = ledger(self.cwd, "budget")
        self.assertEqual(res.returncode, 0)
        self.assertIn("判定不能", res.stdout)
        self.assertNotIn("委譲回数: 0", res.stdout)

    def test_budget_says_unknown_when_payload_schema_is_unrecognised(self):
        ledger(self.cwd, "init", "--force", "--tier", "haiku",
               "--max-delegations", "3", "--claim", "C1=x")
        log = self.cwd / ".jen/logs/tool-events.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text('{"unexpected":"shape"}\n', encoding="utf-8")
        res = ledger(self.cwd, "budget")
        self.assertIn("判定不能", res.stdout)

    def test_budget_counts_delegations_from_the_real_log(self):
        ledger(self.cwd, "init", "--force", "--tier", "haiku",
               "--max-delegations", "3", "--claim", "C1=x")
        log = self.cwd / ".jen/logs/tool-events.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps({"event": "PostToolUse", "data": {"tool_name": n}})
                 for n in ("Agent", "Agent", "Bash", "Read", "Task")]
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        res = ledger(self.cwd, "budget")
        self.assertEqual(res.returncode, 0, "上限3に対し3回なので超過ではない")
        self.assertIn("委譲回数: 3", res.stdout)

    def test_budget_flags_overage_without_hard_stopping(self):
        ledger(self.cwd, "init", "--force", "--tier", "haiku",
               "--max-delegations", "1", "--claim", "C1=x")
        log = self.cwd / ".jen/logs/tool-events.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("\n".join(
            json.dumps({"event": "PostToolUse", "data": {"tool_name": "Agent"}})
            for _ in range(3)) + "\n", encoding="utf-8")
        res = ledger(self.cwd, "budget")
        self.assertEqual(res.returncode, 1)
        self.assertIn("上限超過", res.stderr)
        self.assertIn("強制停止はしない", res.stderr,
                      "v3.4 以来の不変条件（数値による hard-stop はしない）が守られていない")
        # 超過しても gate の判断は被覆だけで決まること
        ledger(self.cwd, "run", "--claim", "C1", "--cmd", "true")
        self.assertEqual(ledger(self.cwd, "gate").returncode, 0,
                         "予算超過がゲートを塞いでしまっている（被覆とは独立であるべき）")

    def test_artifact_evidence_is_medium_not_strong(self):
        (self.cwd / "report.txt").write_text("test output", encoding="utf-8")
        ledger(self.cwd, "attest", "--claim", "C1", "--kind", "artifact", "--ref", "report.txt")
        ev = read_doc(self.cwd)["claims"]["C1"]["evidence"][0]
        self.assertEqual(ev["strength"], "medium",
                         "エージェントが書けるファイルが strong に分類された")
        self.assertIn("sha256", ev)


if __name__ == "__main__":
    unittest.main(verbosity=2)
