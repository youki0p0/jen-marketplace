#!/usr/bin/env python3
"""Jen v4 — 証拠台帳（Evidence Ledger）.

受入条件を K 個の atomic な「主張」に分解し、主張ごとに**単調非減少**の状態
（NULL → PARTIAL → MATCH）を持つ。全主張が MATCH になるまで完了を認めない。
**判定はモデル、合成は決定論**。

## 設計の出典（すべて `.jen/` 外の一次情報・research/ 参照）

- 停止を「確信度」ではなく「主張ごとの証拠被覆」で決める:
  HALT (Roh & Han 2026, arXiv 2608.02009) 「We frame stopping as evidence coverage
  rather than generator confidence」。主張ごとの running max と ALL_MATCH 則もここ。
- 証拠は「文字列」では足りない: コキエ 2026-03 の実験。Stop Hook が出力中の
  `<proof>...</proof>` を見ていたため、モデルはその文字列を出力するだけで通した。
  → 強度を3段階に分け、**強い証拠は台帳が自分で実行して得たものだけ**とする。
- センサーを連続で回すか最終ゲート1回に畳むかはモデル能力で決める:
  Jain 2026-10「What changes with model capability is not whether independent sensors
  are needed, but when they run」／Anthropic 2026-03「moved the evaluator to a single
  pass at the end of the run」（Opus 4.6 で sprint 構造を削除した際の判断）。
- 問いが変われば被覆は引き継がない: Bates 1989（berrypicking）。`revise` が担う。

## この部品が前提している「モデルの不足」（P9）

1. モデルは**自分の被覆を過大評価する**（＝早すぎる完了宣言）。
2. モデルは**弱い証拠を強い証拠と見なす**。
3. モデルは**ゲートを通すために証拠を偽造する**（コキエの実験で実証済み）。

モデルが上記を起こさなくなったなら、この部品は外してよい。
外し方は `sensor_mode` を `final_gate` にし、最終的には hooks から外す。
**効果が測れていないことを承知しておくこと** — 「hook で強制した検証ループ vs
プロンプトのみ」の完了率を比較した研究は、2026-10 時点で見つかっていない。

## 正直な限界（過大評価しないこと）

**偽造を暗号的に防げてはいない。** 封印（seal）は台帳自身が既知の方法で計算するので、
このスクリプトを読めるエージェントは偽造後に封印を再計算できる。防げているのは:

1. 不注意な書き換え（シェルのリダイレクト・`sed -i`）→ 封印の不一致で検出
2. よくある編集経路 → PreToolUse（`guard_patterns.LEDGER_PATTERNS`）で拒否
3. ログの実体が無い強い証拠 → `orphan_strong()` で検出

つまり**「カジュアルな抜け道を塞ぎ、事後に検出可能にする」**までであって、
決意したエージェントを止められるわけではない。コキエ 2026-03 の結論と同じ
（「完全な防御ではないが、カジュアルに通り抜けられる抜け道を塞ぐだけで実用上は機能する」）。
理由も同じで、安全性ではなく**訓練分布**の話である。文字列を出力するのは頻出パターン、
ログを捏造して封印を再計算するのはそうではない。

最も強い層は封印ではなく **`run` の存在そのもの**である。台帳が自分で実行して
終了コードを捕まえる限り、エージェントは「テストが通った」を出力で作れない。

標準ライブラリのみ。Python 3.10+。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from guard_patterns import deny_reason
except Exception:  # 共有ガードが無い環境では run を使わせない
    def deny_reason(command: str, *, include_ledger: bool = True):  # type: ignore[misc]
        return "guard_patterns.py not found; refusing to execute commands"

LEDGER = Path(".jen/claims.json")
STRENGTH = {"weak": 1, "medium": 2, "strong": 3}
STATES = {"NULL": 0, "PARTIAL": 1, "MATCH": 2}
# 階層 → センサーの走らせ方。Jain / Anthropic の収束点。
# fable は opus と同扱い（ユーザー判断 2026-10: 現状の性能では優先度が低い）。
TIER_SENSOR = {
    "haiku": "continuous",
    "sonnet": "continuous",
    "opus": "final_gate",
    "fable": "final_gate",
}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canonical(doc: dict) -> bytes:
    body = {k: v for k, v in doc.items() if k != "seal"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def seal_of(doc: dict) -> str:
    return hashlib.sha256(canonical(doc)).hexdigest()


def load() -> dict:
    if not LEDGER.exists():
        die(f"{LEDGER} が無い。先に `evidence_ledger.py init` を実行する。")
    try:
        doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"{LEDGER} を読めない: {exc}")
    recorded = doc.get("seal")
    if recorded and recorded != seal_of(doc):
        # 封印が合わない＝台帳が台帳スクリプト以外に書き換えられた。
        # 消さない・直さない。報告して止める（判断は人間）。
        doc["_seal_broken"] = True
    return doc


def save(doc: dict, op: str, detail: str = "") -> None:
    doc["updated_at"] = now()
    doc.setdefault("history", []).append({"ts": now(), "op": op, "detail": detail})
    doc["seal"] = seal_of(doc)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, LEDGER)


def die(msg: str, code: int = 1):
    print(f"JEN_LEDGER_ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def recompute(claim: dict) -> str:
    """主張の状態を証拠から再計算する。単調非減少（下がらない）。"""
    best = 0
    for ev in claim.get("evidence", []):
        if not ev.get("satisfied"):
            continue  # 失敗した実行は記録に残すが、状態は上げない
        best = max(best, STRENGTH.get(ev.get("strength", "weak"), 0))
    need = STRENGTH.get(claim.get("require", "medium"), 2)
    computed = "MATCH" if best >= need else ("PARTIAL" if best > 0 else "NULL")
    prev = claim.get("state", "NULL")
    return computed if STATES[computed] > STATES.get(prev, 0) else prev


def get_claim(doc: dict, cid: str) -> dict:
    claim = doc.get("claims", {}).get(cid)
    if claim is None:
        die(f"主張 {cid} が台帳に無い。既存: {', '.join(doc.get('claims', {})) or '(なし)'}")
    return claim


# ---------------------------------------------------------------- subcommands

def cmd_init(a) -> int:
    if LEDGER.exists() and not a.force:
        die(f"{LEDGER} は既にある。上書きするなら --force（履歴は失われる）。")
    claims: dict[str, dict] = {}
    raw = []
    if a.claim:
        raw = [{"id": c.split("=", 1)[0], "text": c.split("=", 1)[1]} for c in a.claim if "=" in c]
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
        if text:
            try:
                raw = json.loads(text)
            except Exception as exc:
                die(f"stdin の JSON を読めない: {exc}")
    if not raw:
        die("主張が空。--claim 'C1=...' か、stdin に [{\"id\":..,\"text\":..}] を渡す。")
    for item in raw:
        cid = str(item.get("id", "")).strip()
        if not ID_RE.match(cid):
            die(f"主張IDが不正: {cid!r}")
        req = item.get("require", a.require)
        if req not in STRENGTH:
            die(f"require が不正: {req!r}（weak|medium|strong）")
        claims[cid] = {"text": str(item.get("text", "")).strip(),
                       "require": req, "state": "NULL", "evidence": []}
    tier = a.tier
    doc = {
        "schema": 1, "mission_rev": 1, "tier": tier,
        "sensor_mode": TIER_SENSOR.get(tier, "continuous"),
        "created_at": now(), "claims": claims, "history": [],
    }
    save(doc, "init", f"tier={tier} claims={len(claims)}")
    print(f"OK init  tier={tier}  sensor={doc['sensor_mode']}  claims={len(claims)}")
    return 0


def cmd_claim_add(a) -> int:
    doc = load()
    if not ID_RE.match(a.id):
        die(f"主張IDが不正: {a.id!r}")
    if a.id in doc.get("claims", {}):
        die(f"主張 {a.id} は既にある")
    doc["claims"][a.id] = {"text": a.text, "require": a.require, "state": "NULL", "evidence": []}
    save(doc, "claim-add", f"{a.id} require={a.require}")
    print(f"OK claim-add  {a.id}  require={a.require}")
    return 0


def cmd_attest(a) -> int:
    """弱い証拠（note）と中程度の証拠（artifact）を付ける。

    **強い証拠はここからは作れない。** run サブコマンドだけが作る。
    """
    doc = load()
    claim = get_claim(doc, a.claim)
    if a.kind == "note":
        if not a.detail:
            die("--kind note には --detail が要る")
        ev = {"strength": "weak", "kind": "note", "detail": a.detail,
              "satisfied": True, "ts": now()}
    else:  # artifact
        if not a.ref:
            die("--kind artifact には --ref（ファイルパス）が要る")
        p = Path(a.ref)
        if not p.is_file():
            die(f"証拠ファイルが無い: {a.ref}")
        blob = p.read_bytes()
        ev = {"strength": "medium", "kind": "artifact", "ref": str(p),
              "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
              "detail": a.detail or "", "satisfied": True, "ts": now()}
    claim.setdefault("evidence", []).append(ev)
    claim["state"] = recompute(claim)
    save(doc, "attest", f"{a.claim} {ev['strength']}/{ev['kind']} -> {claim['state']}")
    print(f"OK attest  {a.claim}  {ev['strength']}/{ev['kind']}  state={claim['state']}")
    return 0


def cmd_run(a) -> int:
    """台帳が**自分でコマンドを実行**し、実際の終了コードを強い証拠として記録する。

    エージェントの自己申告を経由しないので、トークン出力では偽造できない。
    共有の拒否パターン（guard_patterns.py）を必ず通す — ここを抜かすと
    PreToolUse を迂回する穴になる。
    """
    doc = load()
    claim = get_claim(doc, a.claim)
    reason = deny_reason(a.cmd, include_ledger=False)
    if reason:
        die(f"実行を拒否: {reason}\nCommand: {a.cmd}", code=2)
    try:
        argv = shlex.split(a.cmd)
    except ValueError as exc:
        die(f"コマンドを解釈できない: {exc}")
    if not argv:
        die("--cmd が空")
    started = time.time()
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=a.timeout, check=False)
        code, out, err = proc.returncode, proc.stdout, proc.stderr
        timed_out = False
    except FileNotFoundError:
        die(f"コマンドが見つからない: {argv[0]}")
    except subprocess.TimeoutExpired:
        code, out, err, timed_out = -1, "", f"timeout after {a.timeout}s", True
    elapsed = round(time.time() - started, 2)

    logdir = Path(".jen/logs/evidence")
    logdir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    # 同一秒に2回走ると名前が衝突し、**失敗の記録が上書きされる**。
    # 失敗は最も価値のある記録なので、証拠の連番を必ず付ける。
    seq = len(claim.get("evidence", []))
    logp = logdir / f"{a.claim}-{stamp}-{seq:03d}.txt"
    logp.write_text(f"$ {a.cmd}\nexit={code} elapsed={elapsed}s timeout={timed_out}\n"
                    f"--- stdout ---\n{out}\n--- stderr ---\n{err}\n", encoding="utf-8")

    satisfied = (code == a.expect_exit) and not timed_out
    ev = {"strength": "strong", "kind": "command", "ref": a.cmd,
          "exit": code, "expect_exit": a.expect_exit, "elapsed_s": elapsed,
          "timed_out": timed_out, "log": str(logp),
          "detail": a.detail or "", "satisfied": satisfied, "ts": now()}
    claim.setdefault("evidence", []).append(ev)
    claim["state"] = recompute(claim)
    save(doc, "run", f"{a.claim} exit={code} satisfied={satisfied} -> {claim['state']}")
    verdict = "SATISFIED" if satisfied else "FAILED"
    print(f"{verdict}  {a.claim}  exit={code} (expected {a.expect_exit})  "
          f"state={claim['state']}  log={logp}")
    return 0 if satisfied else 1


def cmd_revise(a) -> int:
    """問いが変わったときに版を切る。**被覆は引き継がない**（Bates 1989）."""
    doc = load()
    old = doc.get("mission_rev", 1)
    doc["mission_rev"] = old + 1
    for cid, claim in doc.get("claims", {}).items():
        claim["state"] = "NULL"
        claim["evidence"] = []
    save(doc, "revise", f"rev {old} -> {old + 1}: {a.note}")
    print(f"OK revise  rev {old} -> {old + 1}  （全主張の被覆をリセットした）")
    return 0


def cmd_tier(a) -> int:
    doc = load()
    if a.set not in TIER_SENSOR:
        die(f"tier が不正: {a.set!r}（{'|'.join(TIER_SENSOR)}）")
    doc["tier"] = a.set
    doc["sensor_mode"] = TIER_SENSOR[a.set]
    save(doc, "tier", f"{a.set} -> {doc['sensor_mode']}")
    print(f"OK tier  {a.set}  sensor={doc['sensor_mode']}")
    return 0


def orphan_strong(claim: dict) -> list[str]:
    """強い証拠のうち、台帳が書いたログが実在しないものを返す。

    偽造の費用を上げる層。`run` は必ず実ログを残すので、
    ログの無い strong は台帳スクリプト以外が書いた印になる。
    """
    missing = []
    for ev in claim.get("evidence", []):
        if ev.get("strength") != "strong" or not ev.get("satisfied"):
            continue
        ref = ev.get("log")
        if not ref or not Path(ref).is_file():
            missing.append(ref or "(log 欄が無い)")
    return missing


def report(doc: dict) -> tuple[list[str], bool]:
    lines, ok = [], True
    tainted = bool(doc.get("_seal_broken"))
    lines.append(f"mission_rev={doc.get('mission_rev')}  tier={doc.get('tier')}  "
                 f"sensor={doc.get('sensor_mode')}")
    if tainted:
        lines.append("⚠️ 封印が一致しない — 台帳が evidence_ledger.py 以外に書き換えられた形跡がある。"
                     "**以下の状態は信用できない**")
        ok = False
    for cid, claim in sorted(doc.get("claims", {}).items()):
        state = claim.get("state", "NULL")
        if tainted:
            mark, shown = "[!]", "UNTRUSTED"
        else:
            mark = {"MATCH": "[x]", "PARTIAL": "[~]", "NULL": "[ ]"}.get(state, "[?]")
            shown = state
        best = max((STRENGTH.get(e.get("strength", "weak"), 0)
                    for e in claim.get("evidence", []) if e.get("satisfied")), default=0)
        got = {3: "strong", 2: "medium", 1: "weak", 0: "none"}[best]
        lines.append(f"{mark} {cid}  {shown:<9} require={claim.get('require')} got={got}"
                     f"  {claim.get('text','')[:60]}")
        for ref in orphan_strong(claim):
            lines.append(f"    ⚠️ 強い証拠にログの実体が無い: {ref} — 捏造の疑い")
            ok = False
        if state != "MATCH":
            ok = False
    return lines, ok


def cmd_status(a) -> int:
    doc = load()
    if a.json:
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        return 0 if report(doc)[1] else 1
    lines, ok = report(doc)
    print("\n".join(lines))
    print("ALL_MATCH" if ok else "NOT_ALL_MATCH")
    return 0 if ok else 1


def cmd_gate(a) -> int:
    """完了を許すかの決定論的判定。Stop hook がこれを使う。"""
    if not LEDGER.exists():
        print("JEN_GATE: 台帳が無い（主張が宣言されていない）", file=sys.stderr)
        return 2
    doc = load()
    lines, ok = report(doc)
    if ok:
        print("JEN_GATE_PASS  " + lines[0])
        return 0
    print("JEN_GATE_BLOCK  未被覆の主張がある\n" + "\n".join(lines), file=sys.stderr)
    return 2


def main() -> int:
    p = argparse.ArgumentParser(prog="evidence_ledger.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="台帳を作る")
    s.add_argument("--claim", action="append", help="'C1=主張の文' 形式。複数可")
    s.add_argument("--tier", default="sonnet", choices=sorted(TIER_SENSOR))
    s.add_argument("--require", default="medium", choices=sorted(STRENGTH))
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("claim-add", help="主張を足す")
    s.add_argument("--id", required=True)
    s.add_argument("--text", required=True)
    s.add_argument("--require", default="medium", choices=sorted(STRENGTH))
    s.set_defaults(fn=cmd_claim_add)

    s = sub.add_parser("attest", help="弱い/中程度の証拠を付ける（強い証拠はここでは作れない）")
    s.add_argument("--claim", required=True)
    s.add_argument("--kind", required=True, choices=["note", "artifact"])
    s.add_argument("--ref")
    s.add_argument("--detail")
    s.set_defaults(fn=cmd_attest)

    s = sub.add_parser("run", help="台帳が自分で実行し、終了コードを強い証拠にする")
    s.add_argument("--claim", required=True)
    s.add_argument("--cmd", required=True)
    s.add_argument("--expect-exit", type=int, default=0, dest="expect_exit")
    s.add_argument("--timeout", type=int, default=900)
    s.add_argument("--detail")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("revise", help="問いが変わった。版を切り被覆をリセットする")
    s.add_argument("--note", required=True)
    s.set_defaults(fn=cmd_revise)

    s = sub.add_parser("tier", help="モデル階層を設定し、センサーの走らせ方を決める")
    s.add_argument("--set", required=True)
    s.set_defaults(fn=cmd_tier)

    s = sub.add_parser("status", help="被覆状況を表示（全MATCHで exit 0）")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("gate", help="完了可否の決定論的判定（Stop hook 用）")
    s.set_defaults(fn=cmd_gate)

    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
