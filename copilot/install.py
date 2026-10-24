#!/usr/bin/env python3
"""Jen for GitHub Copilot — インストーラ（兼ビルダー）.

Claude Code 版 Jen（`plugins/jen` または `plugins/jen-classic`）を**原典**として読み、
GitHub Copilot のカスタマイズ形式へ変換して、対象リポジトリの `.github/` に展開する。

    python3 copilot/install.py --target ~/src/myapp                 # 既定: jen / portable / fable→opus
    python3 copilot/install.py --target . --edition jen-classic     # Lean 版
    python3 copilot/install.py --target . --surface cli --fable     # CLI 向けにモデルを固定、Fable を使う
    python3 copilot/install.py --target . --dry-run                 # 何を書くかだけ表示
    python3 copilot/install.py --target . --uninstall               # 入れたものを外す（手で直したファイルは残す）

## なぜ「コピー」ではなく「変換」か

Copilot 版のファイルをこのリポジトリに複製して持つと、Claude 版を直したときに
片方だけ直る事故が起きる（`tests/check_axiom0.py` が hooks の同一性を機械で縛っているのと
同じ理由）。原典は1つにして、差分（Copilot 固有の読み替え）だけを `copilot/kit/` に置く。

## 展開先

    .github/agents/jen-*.agent.md          18体（frontmatter を Copilot 形式に変換）
    .github/skills/<name>/SKILL.md         jen / jen-review / jen-repair / jen-release / jen-longrun
                                           + 旧コマンド jen-status / jen-board / jen-standup / jen-pr / jen-audit
    .github/skills/jen/references/         参照資料（+ copilot-delta.md）
    .github/skills/jen/scripts/            jen_status.py ほか
    .github/hooks/jen.json                 userPromptSubmitted / preToolUse / postToolUse / agentStop
    .github/hooks/jen/*.py                 Claude 版 hooks（そのまま）+ Copilot アダプタ
    .github/instructions/jen.instructions.md   `.jen/**` を触るときの規則（--no-instructions で省略）
    .github/jen-copilot.lock.json          入れたファイルとハッシュ（更新・アンインストール用）

標準ライブラリのみ。Python 3.10+。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
KIT = HERE / "kit"
LOCK_REL = ".github/jen-copilot.lock.json"
KIT_REV = 1
BODY_LIMIT = 30_000          # custom agent の本文上限（文字数・custom-agents-configuration）
SKILL_DESC_LIMIT = 1024      # Agent Skills の description 上限
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")  # VS Code は小文字・数字・ハイフンのみ

# Claude Code のツール名 → Copilot のツール別名（大文字小文字は無視される）
TOOL_MAP = {
    "read": "read", "notebookread": "read",
    "write": "edit", "edit": "edit", "multiedit": "edit", "notebookedit": "edit",
    "bash": "execute",
    "grep": "search", "glob": "search",
    "agent": "agent", "task": "agent",
    "websearch": "web", "webfetch": "web",
    "todowrite": "todo",
}
# Claude の effort → Copilot の推論強度（VS Code: reasoning-effort / CLI: reasoningEffort）
EFFORT_OK = {"low", "medium", "high", "xhigh", "max"}

USER_INVOCABLE = {"jen-pmo"}
# Copilot では jen-pmo を直接選ぶのが標準なので、伝言役前提の一文だけ差し替える
DESCRIPTION_REWRITES = {
    "jen-pmo": (
        ("The main session must not orchestrate; it only relays verbatim input here.",
         "Select this agent directly (agent picker, --agent jen-pmo, or as the cloud agent's custom agent); "
         "any other agent must only relay the user's verbatim input here."),
    ),
}
COMMAND_SKILLS = ("jen-status", "jen-board", "jen-standup", "jen-pr", "jen-audit")
SOURCE_SKILLS = ("jen-review", "jen-repair", "jen-release", "jen-longrun")

COMMON_NOTE = (
    "> ⚙️ **Copilot 版**: あなたは jen-pmo から subagent として起動される。"
    "ユーザーへ直接質問しない（必要なら質問文を返して止まる）。さらなる委譲はしない。"
    "ツール名・パス・Human Gate の読み替えは `.github/skills/jen/references/copilot-delta.md` に従う。\n"
)
WORKTREE_NOTE = (
    "> ⚠️ Claude 版の `isolation: worktree` は Copilot に無い。他の worker と同じ作業ツリーを共有しているので、"
    "委譲 prompt で指定されたファイル以外を変更しない。\n"
)
FABLE_NOTE = (
    "> ℹ️ この agent の原典は fable 層。この環境では {model} に展開されている"
    "（Fable 系は組織での有効化が必要なため。`install.py --fable` で変更できる）。\n"
)
SKILL_NOTES = {
    "jen-longrun": (
        "\n## Copilot 版での運用\n\n"
        "- 多日規模の自走は **cloud agent** が向いている（CLI の `/delegate`、または Issue を Copilot に割り当てて"
        "カスタムエージェント `jen-pmo` を選ぶ）。非対話・権限は事前付与・`copilot/*` ブランチに push される。\n"
        "- cloud agent には人間がいない。Human Gate は `.jen/human-gate.md` と PR 本文に書いて停止する。\n"
        "- 完了ゲート（agentStop）が強制する追加ターンもジョブ時間に数えられる。差し戻しが続いたら粘らず止まる。\n"
        "- 詳細: `.github/skills/jen/references/copilot-delta.md` の §8。\n"
    ),
}
COMMAND_PREPEND = {
    "jen-audit": (
        "> ⚙️ **Copilot 版**: プラグインルートはリポジトリの `.github/` で固定。下の `echo $CLAUDE_PLUGIN_ROOT` は不要で、"
        "scout へは `.github/` を棚卸し対象として渡す。\n\n"
    ),
}


# ---------------------------------------------------------------- frontmatter

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Jen のファイルで使っている YAML の小さな部分集合だけを読む.

    対応: `key: value` / `key: >-`（後続のインデント行を空白で連結）/ 引用符付き文字列。
    それ以外の形が来たら黙って誤読せず例外にする。
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("frontmatter が閉じていない")
    head, body = text[4:end], text[end + 4:].lstrip("\n")
    meta: dict[str, str] = {}
    key = None
    for line in head.splitlines():
        if not line.strip():
            continue
        if line.startswith((" ", "\t")) and key:
            meta[key] = (meta[key] + " " + line.strip()).strip()
            continue
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if not m:
            raise ValueError(f"frontmatter の行を解釈できない: {line!r}")
        key, val = m.group(1), m.group(2).strip()
        if val in (">-", ">", "|", "|-"):
            val = ""
        elif len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        meta[key] = val
    return meta, body


def yq(value) -> str:
    """YAML の値として安全な表記（JSON 文字列は YAML の二重引用符文字列として有効）."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(v, ensure_ascii=False) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False)


def emit(meta: list[tuple[str, object]], body: str) -> str:
    lines = ["---"] + [f"{k}: {yq(v)}" for k, v in meta if v is not None] + ["---", ""]
    return "\n".join(lines) + body.rstrip("\n") + "\n"


# ---------------------------------------------------------------- rewrites

def rewrite_paths(text: str) -> str:
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/hooks/", ".github/hooks/jen/")
    text = text.replace("$CLAUDE_PLUGIN_ROOT/hooks/", ".github/hooks/jen/")
    text = text.replace("../skills/jen/references/", ".github/skills/jen/references/")
    text = re.sub(r"(?<![\w/.])references/", ".github/skills/jen/references/", text)
    text = re.sub(r"(?<![\w/.])scripts/jen_", ".github/skills/jen/scripts/jen_", text)
    text = text.replace("/jen:jen-", "/jen-").replace("/jen:jen ", "/jen ")
    return text


def map_tools(raw: str) -> list[str]:
    out: list[str] = []
    for t in (x.strip() for x in raw.split(",")):
        if not t:
            continue
        mapped = TOOL_MAP.get(t.lower())
        if mapped is None:
            raise ValueError(f"Copilot への対応が未定義のツール: {t}")
        if mapped not in out:
            out.append(mapped)
    return out


# ---------------------------------------------------------------- builders

class Build:
    def __init__(self, edition: str, surface: str, fable: bool, instructions: bool):
        self.edition, self.surface, self.fable, self.instructions = edition, surface, fable, instructions
        self.src = REPO / "plugins" / edition
        if not (self.src / "agents").is_dir():
            raise SystemExit(f"原典が見つからない: {self.src}")
        self.models = json.loads((HERE / "models.json").read_text(encoding="utf-8"))
        self.files: dict[str, bytes] = {}
        self.resolved: dict[str, object] = {}
        self.warnings: list[str] = []

    def put(self, rel: str, data: str | bytes) -> None:
        self.files[rel] = data.encode("utf-8") if isinstance(data, str) else data

    # モデル階層 → (model 値, 実際に使う階層)
    def model_for(self, tier: str):
        tier = tier.strip().lower()
        if tier not in self.models["id"]:
            raise ValueError(f"未知のモデル階層: {tier}")
        effective = tier if (tier != "fable" or self.fable) else self.models["fallback"]["fable"]
        style = "vscode" if self.surface == "vscode" else "id"
        names = self.models[style]
        chain = [names[effective]]
        if effective == "fable":  # --fable 指定時のみ。使えない環境では opus に落とす
            chain.append(names[self.models["fallback"]["fable"]])
        self.resolved[tier] = chain if len(chain) > 1 else chain[0]
        return chain, effective

    def agent(self, path: Path) -> None:
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        name = meta["name"]
        tier = meta.get("model", "sonnet")
        chain, effective = self.model_for(tier)
        desc = meta["description"]
        for old, new in DESCRIPTION_REWRITES.get(name, ()):
            desc = desc.replace(old, new)
        fm: list[tuple[str, object]] = [
            ("name", name),
            ("description", desc),
            ("tools", map_tools(meta.get("tools", ""))),
        ]
        if self.surface == "vscode":
            fm.append(("model", chain if len(chain) > 1 else chain[0]))
        else:
            fm.append(("model", chain[0]))
        if self.surface == "cli":
            # AXIOM-0（判断は Claude のみ）を CLI では機械で守る: 宣言外のモデルへ黙って落ちない
            fm += [("models", chain), ("modelPolicy", "required")]
        effort = meta.get("effort")
        if effort in EFFORT_OK:
            if self.surface == "vscode":
                fm.append(("reasoning-effort", effort))
            elif self.surface == "cli":
                fm.append(("reasoningEffort", effort))
        fm.append(("user-invocable", name in USER_INVOCABLE))

        notes = ""
        prepend = KIT / "agents" / f"{name}.prepend.md"
        if prepend.is_file():
            notes += prepend.read_text(encoding="utf-8")
        if name not in USER_INVOCABLE:
            notes += COMMON_NOTE
        if meta.get("isolation") == "worktree":
            notes += WORKTREE_NOTE
        if tier == "fable" and effective != "fable":
            notes += FABLE_NOTE.format(model=chain[0])
        header = (f"<!-- generated by copilot/install.py from plugins/{self.edition}/agents/{path.name}"
                  f" — 直接編集しない（再インストールで上書きされる） -->\n\n")
        text = header + notes + ("\n" if notes else "") + rewrite_paths(body)
        if len(text) > BODY_LIMIT:
            raise ValueError(f"{name}: 本文 {len(text)} 文字が上限 {BODY_LIMIT} を超える")
        self.put(f".github/agents/{name}.agent.md", emit(fm, text))

    def skill(self, name: str, meta: dict, body: str, origin: str) -> None:
        if not SKILL_NAME_RE.match(name):
            raise ValueError(f"skill 名 {name!r} は VS Code で読めない（小文字・数字・ハイフンのみ）")
        desc = meta.get("description", "").replace("Claude Code", "Copilot")
        if not desc or len(desc) > SKILL_DESC_LIMIT:
            raise ValueError(f"skill {name}: description が空か {SKILL_DESC_LIMIT} 文字超")
        fm: list[tuple[str, object]] = [("name", name), ("description", desc)]
        if meta.get("argument-hint"):
            fm.append(("argument-hint", meta["argument-hint"]))
        if meta.get("disable-model-invocation") in ("true", True):
            fm.append(("disable-model-invocation", True))
        header = f"<!-- generated by copilot/install.py from {origin} — 直接編集しない -->\n\n"
        text = header + COMMAND_PREPEND.get(name, "") + rewrite_paths(body) + SKILL_NOTES.get(name, "")
        self.put(f".github/skills/{name}/SKILL.md", emit(fm, text))

    def build(self) -> dict[str, bytes]:
        for p in sorted((self.src / "agents").glob("*.md")):
            self.agent(p)

        # 入口スキルは Copilot 用に書き直したものを使う（伝言役の位置づけが変わるため）
        meta, body = parse_frontmatter((KIT / "skills" / "jen" / "SKILL.md").read_text(encoding="utf-8"))
        self.skill("jen", meta, body, "copilot/kit/skills/jen/SKILL.md")
        for name in SOURCE_SKILLS:
            p = self.src / "skills" / name / "SKILL.md"
            meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
            self.skill(name, meta, body, f"plugins/{self.edition}/skills/{name}/SKILL.md")
        for name in COMMAND_SKILLS:
            p = self.src / "commands" / f"{name}.md"
            meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
            meta.setdefault("disable-model-invocation", "true")  # コマンドは人間が呼ぶもの
            self.skill(name, meta, body, f"plugins/{self.edition}/commands/{name}.md")

        for p in sorted((self.src / "skills" / "jen" / "references").glob("*.md")):
            self.put(f".github/skills/jen/references/{p.name}", rewrite_paths(p.read_text(encoding="utf-8")))
        self.put(".github/skills/jen/references/copilot-delta.md",
                 (KIT / "references" / "copilot-delta.md").read_bytes())
        for p in sorted((self.src / "skills" / "jen" / "scripts").iterdir()):
            if p.is_file():
                self.put(f".github/skills/jen/scripts/{p.name}", p.read_bytes())

        # hooks: Claude 版はそのまま（判定ロジックの単一の正）、Copilot 形式への翻訳はアダプタ
        for p in sorted((self.src / "hooks").glob("*.py")):
            self.put(f".github/hooks/jen/{p.name}", p.read_bytes())
        for p in sorted((KIT / "hooks").glob("copilot_*.py")):
            self.put(f".github/hooks/jen/{p.name}", p.read_bytes())
        self.put(".github/hooks/jen.json", (KIT / "hooks" / "jen.json").read_bytes())

        if self.instructions:
            self.put(".github/instructions/jen.instructions.md",
                     (KIT / "instructions" / "jen.instructions.md").read_bytes())
        return self.files


# ---------------------------------------------------------------- apply

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jen_version() -> str:
    pj = REPO / "plugins" / "jen" / ".claude-plugin" / "plugin.json"
    return json.loads(pj.read_text(encoding="utf-8")).get("version", "0")


def load_lock(target: Path) -> dict:
    p = target / LOCK_REL
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def install(a) -> int:
    target = Path(a.target).resolve()
    if not target.is_dir():
        print(f"対象が無い: {target}", file=sys.stderr)
        return 1
    b = Build(a.edition, a.surface, a.fable, not a.no_instructions)
    files = b.build()
    old = load_lock(target).get("files", {})

    plan: list[tuple[str, str]] = []
    conflicts: list[str] = []
    for rel, data in sorted(files.items()):
        dest = target / rel
        if not dest.exists():
            plan.append(("add", rel))
            continue
        cur = dest.read_bytes()
        if cur == data:
            plan.append(("same", rel))
        elif old.get(rel) == sha(cur):
            plan.append(("update", rel))       # 前回入れたまま手を入れていない
        elif a.force:
            plan.append(("overwrite", rel))
        else:
            conflicts.append(rel)
    stale = [rel for rel in old if rel not in files]

    for op, rel in plan:
        if op != "same":
            print(f"{op:9s} {rel}")
    for rel in stale:
        print(f"{'remove':9s} {rel}   （新しい版には無い）")
    if conflicts:
        print("\n次のファイルは既にあり、Jen が入れたものではないか手で変更されている:", file=sys.stderr)
        for rel in conflicts:
            print(f"  {rel}", file=sys.stderr)
        print("上書きしてよければ --force を付ける。", file=sys.stderr)
        return 1
    for w in b.warnings:
        print(f"注意: {w}", file=sys.stderr)
    if a.dry_run:
        print(f"\n(dry-run) {len(files)} ファイル。書き込みはしていない。")
        return 0

    for op, rel in plan:
        if op == "same":
            continue
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(files[rel])
    for rel in stale:
        p = target / rel
        if p.is_file() and sha(p.read_bytes()) == old[rel]:
            p.unlink()

    lock = {
        "jen_version": jen_version(), "kit_rev": KIT_REV,
        "edition": a.edition, "surface": a.surface, "fable": a.fable,
        "models": b.resolved,
        "files": {rel: sha(data) for rel, data in sorted(files.items())},
    }
    (target / LOCK_REL).write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    gi = target / ".gitignore"
    ignored = gi.is_file() and any(l.strip() in (".jen", ".jen/", "/.jen/", "/.jen")
                                   for l in gi.read_text(encoding="utf-8").splitlines())
    if a.gitignore and not ignored:
        with gi.open("a", encoding="utf-8") as fh:
            fh.write(("" if not gi.is_file() or gi.read_text(encoding="utf-8").endswith("\n") else "\n")
                     + ".jen/\n")
        ignored = True

    print(f"\n✔ Jen {lock['jen_version']} ({a.edition}) を {target} に展開した。"
          f" surface={a.surface} fable={'on' if a.fable else 'off(→opus)'}")
    if not ignored:
        print("⚠️ .jen/ が .gitignore に無い。ツールログに secret が載り得るので追加すること"
              "（--gitignore で自動追記できる）。", file=sys.stderr)
    print("次: エージェント一覧から jen-pmo を選んでゴールを渡す。"
          " 最初に1回、.jen/ を作っておくと最初の入力から hook が原文を保存する: mkdir .jen")
    return 0


def uninstall(a) -> int:
    target = Path(a.target).resolve()
    lock = load_lock(target)
    if not lock:
        print(f"{LOCK_REL} が無い。Jen が入っていないか、手で入れられている。", file=sys.stderr)
        return 1
    kept: list[str] = []
    for rel, digest in lock.get("files", {}).items():
        p = target / rel
        if not p.is_file():
            continue
        if sha(p.read_bytes()) == digest or a.force:
            print(f"remove    {rel}")
            if not a.dry_run:
                p.unlink()
        else:
            kept.append(rel)
    if not a.dry_run:
        (target / LOCK_REL).unlink()
        for d in sorted({(target / r).parent for r in lock.get("files", {})}, key=lambda x: -len(x.parts)):
            try:
                d.rmdir()  # 空になったディレクトリだけ消える
            except OSError:
                pass
    for rel in kept:
        print(f"keep      {rel}   （手で変更されているので残した。--force で削除）", file=sys.stderr)
    print("`.jen/`（実行時の状態）には触れていない。")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Jen を GitHub Copilot 形式でリポジトリに展開する")
    p.add_argument("--target", required=True, help="展開先リポジトリのルート")
    p.add_argument("--edition", choices=("jen", "jen-classic"), default="jen")
    p.add_argument("--surface", choices=("portable", "cli", "vscode"), default="portable",
                   help="portable=モデルIDのみ（cloud agent/CLI/VS Code 共通）, "
                        "cli=modelPolicy:required でモデル固定, vscode=表示名＋推論強度")
    p.add_argument("--fable", action="store_true", help="fable 層を Fable で動かす（組織での有効化が必要）")
    p.add_argument("--no-instructions", action="store_true", help=".github/instructions/jen.instructions.md を入れない")
    p.add_argument("--gitignore", action="store_true", help="対象の .gitignore に .jen/ を追記する")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="手で変更されたファイルも上書き/削除する")
    p.add_argument("--uninstall", action="store_true")
    a = p.parse_args(argv)
    try:
        return uninstall(a) if a.uninstall else install(a)
    except ValueError as exc:
        print(f"変換できない: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
