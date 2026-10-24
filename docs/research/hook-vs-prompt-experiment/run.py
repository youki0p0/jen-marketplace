#!/usr/bin/env python3
"""Run one trial: python3 run.py TASK COND REP [--model sonnet]

TASK: a directory under tasks/   COND: P0 | P1 | H   (main experiment: --out runs_main, prompt_main.txt)
Creates runs/<TASK>_<COND>_r<REP>/ with work/ (the agent's repo), baseline.json,
transcript.jsonl (stream-json), hooklog.jsonl, meta.json.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

EXP = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
TOOLS = "Bash,Read,Edit,Write,MultiEdit,Glob,Grep"

# Environment variables the nested Claude Code must not inherit: harness memory,
# messaging, extra CLAUDE.md dirs, skills/plugins sync, and unrelated credentials.
DROP_ENV = {
    "CLAUDE_CODE_POST_TURN_MEMORY", "CLAUDE_CODE_POST_TURN_MEMORY_CONFIG",
    "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_REMOTE_SESSION_ID",
    "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD", "CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION",
    "CCR_SKILL_OVERRIDES", "CLAUDE_CODE_SYNC_SKILLS", "CLAUDE_CODE_SYNC_PLUGINS",
    "CLAUDE_CODE_CCR_EARLY_PLUGINS_SYNC", "CLAUDE_CODE_TERMINAL_MCP_TOOLS",
    "GH_TOKEN", "GITHUB_TOKEN", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "CLOUDSDK_AUTH_ACCESS_TOKEN",
}
DROP_PREFIX = ("CLAUDE_CODE_ARTIFACT",)


def hashes(root):
    out = {}
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            p = os.path.join(d, f)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, root)] = hashlib.sha256(fh.read()).hexdigest()
    return out


def clean_env():
    env = {k: v for k, v in os.environ.items()
           if k not in DROP_ENV and not k.startswith(DROP_PREFIX)}
    return env


def build_prompt(cond, prompt_set="main"):
    base = "prompt_main.txt" if prompt_set == "main" else "prompt_base.txt"
    with open(os.path.join(EXP, "conditions", base)) as f:
        p = f.read()
    if cond == "P1":
        with open(os.path.join(EXP, "conditions", "prompt_p1_suffix.txt")) as f:
            p += f.read()
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("cond", choices=["P0", "P1", "H"])
    ap.add_argument("rep", type=int)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--budget", default="2")
    ap.add_argument("--prompt-set", choices=["main", "pilot"], default="main")
    ap.add_argument("--out", default="runs_main", help="runs root, relative to the experiment dir")
    a = ap.parse_args()

    rid = f"{a.model}_{a.task}_{a.cond}_r{a.rep}"
    rd = os.path.join(EXP, a.out, a.model, f"{a.task}_{a.cond}_r{a.rep}")
    os.makedirs(os.path.dirname(rd), exist_ok=True)
    if os.path.exists(rd):
        raise SystemExit(f"{rd} exists; refusing to overwrite")
    work = os.path.join(rd, "work")
    shutil.copytree(os.path.join(EXP, "tasks", a.task, "repo"), work)
    if a.cond == "H":
        shutil.copytree(os.path.join(EXP, "conditions", "H_claude"), os.path.join(work, ".claude"))
    git = ["git", "-c", "user.name=exp", "-c", "user.email=exp@example.invalid"]
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    subprocess.run(git + ["add", "-A"], cwd=work, check=True)
    subprocess.run(git + ["commit", "-q", "-m", "initial"], cwd=work, check=True)
    with open(os.path.join(rd, "baseline.json"), "w") as f:
        json.dump(hashes(work), f, indent=1)

    env = clean_env()
    env["EXP_HOOKLOG"] = os.path.join(rd, "hooklog.jsonl")
    env["EXP_BASELINE"] = os.path.join(rd, "baseline.json")
    prompt = build_prompt(a.cond, a.prompt_set)
    cmd = ["claude", "-p", prompt, "--model", a.model,
           "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project", "--strict-mcp-config",
           "--tools", TOOLS, "--allowedTools", TOOLS,
           "--disallowedTools", "mcp__claude-in-chrome", "--disable-slash-commands",
           "--permission-mode", "acceptEdits",
           "--max-budget-usd", a.budget,
           "--no-session-persistence"]
    t0 = time.time()
    timed_out = False
    with open(os.path.join(rd, "transcript.jsonl"), "w") as out, \
            open(os.path.join(rd, "stderr.txt"), "w") as err:
        try:
            p = subprocess.run(cmd, cwd=work, env=env, stdout=out, stderr=err,
                               stdin=subprocess.DEVNULL, timeout=a.timeout)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc, timed_out = None, True
    meta = {"run": rid, "task": a.task, "cond": a.cond, "rep": a.rep, "model": a.model,
            "prompt_set": a.prompt_set, "rc": rc, "timed_out": timed_out, "wall_s": round(time.time() - t0, 1),
            "prompt": prompt, "cmd": cmd[:2] + ["<prompt>"] + cmd[3:]}
    with open(os.path.join(rd, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: meta[k] for k in ("run", "rc", "timed_out", "wall_s")}))


if __name__ == "__main__":
    main()
