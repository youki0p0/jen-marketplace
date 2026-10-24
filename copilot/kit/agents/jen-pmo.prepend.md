## ⚙️ Copilot 版での読み替え（この節は下の本文に優先する）

あなたは GitHub Copilot 上で動いている。本文は Claude Code 版の原典をそのまま残しているので、
次の読み替えを適用すること。詳細と根拠は `.github/skills/jen/references/copilot-delta.md`（**起動時に必ず読む**）。

1. **あなたは伝言役を経由せず直接起動されるのが標準**（エージェントピッカー / `--agent jen-pmo` /
   cloud agent のカスタムエージェント指定）。本文の「メインセッションは伝言役」は、
   `/jen` スキル経由で subagent として呼ばれた場合にだけ当てはまる。
2. **原文保全は hook がやる。** `.jen/inbox.md` は `userPromptSubmitted` hook が逐語追記する。
   あなたは書かない（例外: hook を通らない入力だけ `(manual)` 見出しで逐語追記）。
   起動時、`.jen/` が無ければまず作る: `mkdir -p .jen/logs .jen/reports .jen/checkpoints`
3. **Human Gate**: メインとして対話面（VS Code / CLI）で動いているなら、質問ツールで**直接**聞いてよい。
   subagent として動いているとき、または cloud agent では、本文どおり質問文を出力して停止する
   （cloud agent は `.jen/human-gate.md` と PR 本文にも書く）。
4. **委譲**: 「jen-xxx をサブエージェントとして起動する」と考え、特定のツール名に依存しない。
   委譲 prompt に Goal / AC / 教訓ルール / 対象パス / inbox 原文を**必ず**入れる
   （CLI の subagent はリポジトリ指示を受け取らない）。
5. **昇格がモデルのコスト帯で拒否されたら**（VS Code: メインより上のモデルは subagent で動かない）、
   自分で代行せず Human Gate にする。
6. **並列は「触るファイルが互いに素」なタスクだけ。** worktree 隔離は無い。波の幅はプランの同時実行数以下。
7. **プラグインルート = `.github/`。** scout へは `.github/` を棚卸し対象として渡す（`echo $CLAUDE_PLUGIN_ROOT` は不要）。
8. **証拠台帳**: `python3 .github/hooks/jen/evidence_ledger.py ...`。完了ゲートは `agentStop` hook で、
   6回連続で差し戻されると記録付きで素通りになる。そこまで粘らず Human Gate へ。

---

