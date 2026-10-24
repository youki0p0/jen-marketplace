#!/usr/bin/env python3
"""Main experiment batch (resumable): python3 batch_main.py [--parallel 4] [--reps 5]

6 tasks x 3 conditions x REPS x {haiku, sonnet}. A trial whose claims.json exists is skipped;
a trial interrupted mid-way is moved to <root>/_incomplete/ and re-run.
Progress lines go to <root>/_progress.log.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

EXP = os.path.dirname(os.path.abspath(__file__))
TASKS = ["A_invoice", "C_money", "D_dates", "E_report", "B_slugify", "F_invoice_ok"]
CONDS = ["P0", "P1", "H"]
MODELS = ["haiku", "sonnet"]


def log(root, msg):
    with open(os.path.join(root, "_progress.log"), "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def one(root, rel, model, task, cond, rep):
    d = os.path.join(root, model, f"{task}_{cond}_r{rep}")
    tag = f"{model} {task} {cond} r{rep}"
    py = sys.executable
    try:
        if os.path.exists(os.path.join(d, "claims.json")):
            return
        if os.path.exists(d) and not os.path.exists(os.path.join(d, "meta.json")):
            dst = os.path.join(root, "_incomplete", f"{model}_{task}_{cond}_r{rep}_{int(time.time())}")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(d, dst)
        if not os.path.exists(d):
            subprocess.run([py, "run.py", task, cond, str(rep), "--model", model, "--out", rel],
                           cwd=EXP, check=True, capture_output=True, text=True)
        if not os.path.exists(os.path.join(d, "judge.json")):
            subprocess.run([py, "judge.py", d], cwd=EXP, check=True, capture_output=True, text=True)
        subprocess.run([py, "claims.py", "--model", "sonnet", d], cwd=EXP, check=True,
                       capture_output=True, text=True)
        log(root, "DONE " + tag)
    except subprocess.CalledProcessError as e:
        log(root, f"FAIL {tag}: {e.cmd[1]} rc={e.returncode} {(e.stderr or '')[-300:]!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs_main")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--reps", type=int, default=5)
    a = ap.parse_args()
    root = os.path.join(EXP, a.out)
    os.makedirs(root, exist_ok=True)
    jobs = [(m, t, c, r) for r in range(1, a.reps + 1) for t in TASKS for c in CONDS for m in MODELS]
    log(root, f"START {len(jobs)} trials")
    with ThreadPoolExecutor(a.parallel) as ex:
        list(ex.map(lambda j: one(root, a.out, *j), jobs))
    log(root, "ALL DONE")


if __name__ == "__main__":
    main()
