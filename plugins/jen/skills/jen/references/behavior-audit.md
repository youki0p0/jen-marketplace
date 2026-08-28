# Skill Map & Behavior Audit（v3.7）

これまでJenには「成果物(内容)を監査する担当」（verifier / strict-verifier /
security-reviewer / contrarian-reviewer / ux-critic）はいたが、
「PMOが実際に何をしたか(行動)を監査する担当」がいなかった。
Ratio Guard・ループガード・可視化プロトコルの自己点検は、すべて
**PMO自身の自己申告**（`.jen/routing-stats.json`・`.jen/board.md`・
`.jen/decisions.md`）に依存しており、独立した第三者チェックが無かった。

v3.7では、コードマップ担当のjen-scout(haiku)に、Jen自身の構成台帳と
行動監査を兼務させる。

## 1. スキルマップ（`.jen/skillmap.json`）

Jen自身の「何がある」台帳。対象コードベースのcodemap.jsonと対になる、
Jenというシステム自身の地図。

```json
{
  "agents": {
    "jen-architect": { "model": "opus", "role": "難設計・複雑リファクタ・境界判断" }
  },
  "skills": { "jen": "PMO本体", "jen-longrun": "長時間自走" },
  "commands": { "jen-status": "状態表示", "jen-board": "ワークボード表示" },
  "references": { "model-tiering.md": "モデル階層とRatio Guard" },
  "issues": [
    "例: SKILL.mdのルーティング表にjen-xxxが記載されていない",
    "例: model-tiering.mdはjen-architectをopusと記載しているが、
     jen-architect.mdのmodel:はfableになっている"
  ],
  "checked_at": "2026-08-25T10:00:00Z"
}
```

- 目的は**整合性チェック**。ドキュメント間の食い違い（frontmatterの`model:`と
  参照ドキュメントの記載のズレ、ルーティング表の記載漏れ、存在しない
  referenceファイルへのリンクなど）を機械的に突き合わせて`issues`へ列挙する。
  scout自身は直さない — 直すかどうかはPMO/人間の判断。
- 初回はagents/skills/commands/references配下をフルスキャンして構築する。
  以降は該当ファイルに変更があった時だけ差分更新する（コードマップと同じ方針）。
- **棚卸し対象のパス（重要）**: プラグインとしてインストールされた場合、
  agent/skill/command/referenceファイルの実体は `~/.claude/plugins/cache/...`
  配下にあり、ユーザーのプロジェクトcwdからは `plugins/jen/...` のような
  相対パスで見えない。scoutはまず `$CLAUDE_PLUGIN_ROOT`（`Bash: echo
  $CLAUDE_PLUGIN_ROOT`）で自分のプラグインルートを特定し、そこからの
  絶対パスで棚卸しする。Jenのソースリポジトリ自身を直接編集している時
  （このリポジトリで作業する場合）に限り、`plugins/jen/...` のリポジトリ
  相対パスでも成立する。`$CLAUDE_PLUGIN_ROOT`が解決できない場合は
  「未解決のため未実施」と明記し、誤った場所を黙ってスキャンしない。
- **利用可能スキル一覧への応答**: ユーザーが「Jenで使えるスキル/エージェント/
  コマンドは何か」と尋ねたら、PMOはこのスキルマップを構築/参照してから
  回答する（記憶やREADMEの記憶で答えない）。トリガーは `skills/jen/SKILL.md`
  の frontmatter `description` に明記済み。

## 2. 行動監査（`.jen/audit.md`）

**材料は自己申告ではなく、hookが機械的に記録した実ログ**を使う:

- `.jen/logs/tool-events.jsonl`（`post_tool_log.py`, PostToolUse hook。
  全ツール呼び出しを対象に、受け取ったペイロードをそのまま1行JSONで記録する）
- `.jen/logs/stop-events.jsonl`（`stop_append_summary.py`, Stop hook）

これらはLLMの協力に依存しない、Jenで数少ない「本物」のログである
（PreToolUseガードと同じ、hooksによる決定論的な記録）。
> 注意（未確認）: PostToolUseのペイロードの正確なスキーマはClaude Code
> ハーネス側の仕様に依存し、Jen側では検証していない。Task tool呼び出し
> （subagent委譲）の`tool_input`に`subagent_type`や委譲prompt本文が
> 含まれるかはハーネスの実装次第 — 含まれていればそこまで監査できるが、
> 含まれていなければ「委譲が発生したこと」までしか確認できない。
> 監査は実際に取得できたペイロードの中身を見て、できる範囲で判定する。

突き合わせる自己申告側: `.jen/board.md`（やり取り行）、
`.jen/routing-stats.json`（ルーティング学習の記録）、`.jen/decisions.md`。

### 監査観点

| 観点 | 実ログ側 | 自己申告側 | 逸脱の意味 |
|---|---|---|---|
| 可視化コンプライアンス | tool-events.jsonl中のTask委譲件数 | board.mdのやり取り行件数 | 委譲したのにユーザーへ非表示にした（沈黙） |
| Ratio Guard整合性 | tool-events.jsonlから読み取れるagent別呼出回数 | routing-stats.jsonの記録件数 | 昇格の記録漏れ・過少申告 |
| コンテキストスコープ遵守 | 委譲promptの内容（取得できれば） | — | 「全部読んで」的な指示が残っていないか |
| ループガード遵守 | 同一task_idへの近似委譲の反復回数 | board.md上のSTUCK/昇格記録 | ブレーカーが機能せず同じ手を繰り返していないか |

### 判定は3値

- **準拠**: 実ログと自己申告が一致
- **逸脱（証跡付き）**: 実ログの該当行を根拠に不一致を指摘する
- **判定不能（ログ不足）**: ペイロードのスキーマ上、確認できない項目

## 3. 運用ルール

- **強制停止はしない**（v3.4/v3.5/v3.6と同じ理由）。監査は自己点検の一部。
  重大な逸脱（可視化の意図的な隠蔽が疑われる等）はHuman Gate相当として報告する。
- **監査は誰が起動しても良い**。longrunのcheckpoint毎にPMOが依頼するのに
  加えて、`/jen:jen-audit` でユーザーが直接scoutへ依頼できる。
  PMOの自己申告に依存する他の自己点検（Ratio Guard等）と違い、
  ユーザー自身が独立に叩けることが、この監査の一番の価値。
- scoutは監査結果を直さない・忖度しない。見つけた不一致をそのまま書く。

## 4. 正直な限界

- haiku・構造的な突き合わせが前提。「PMOの戦略判断が妥当だったか」のような
  価値判断はscoutの仕事ではない（それはverifier/strict-verifier/人間の領分）。
- 監査対象のログ自体（tool-events.jsonl）の記録漏れ・スキーマ不明を
  scoutが検知することはできない（hookの実装依存）。
- PMOがcheckpoint毎の監査依頼自体をサボった場合、それを検知する仕組みは
  ない。ユーザーが`/jen:jen-audit`を直接叩くのが、それに対する唯一の対抗策。
