## ⚙️ Copilot 版での読み替え（この節は下の本文に優先する）

- **Jen 自身の構成はリポジトリの `.github/` にある**（プラグインキャッシュではない）。
  スキルマップの棚卸し対象は次のとおりで、ルートを依頼元から受け取る必要は無い:
  `.github/agents/jen-*.agent.md`・`.github/skills/*/SKILL.md`・`.github/skills/jen/references/*.md`・
  `.github/hooks/jen.json`。本文の「`$CLAUDE_PLUGIN_ROOT` を受け取る」手順は読み飛ばしてよい。
- 整合性チェックで `model:` を見るときは、エイリアス（haiku/sonnet/opus/fable）ではなく
  インストール時に展開された実モデル名が入っている。対応は `.github/jen-copilot.lock.json` の `models` を正とする。
- 行動監査の材料は同じく `.jen/logs/tool-events.jsonl` と `.jen/logs/stop-events.jsonl`。
  Copilot 版では委譲ツールの名前が `task`（CLI）として記録される。
  `stop-events.jsonl` の `reason:"block_cap"` は「完了ゲートを通らずに終わった」記録なので逸脱として数える。
- 詳細: `.github/skills/jen/references/copilot-delta.md`

---

