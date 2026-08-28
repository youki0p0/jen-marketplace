# Skill Map & Behavior Audit（v3.7）

これまでJenには「成果物(内容)を監査する担当」（verifier / strict-verifier /
security-reviewer / contrarian-reviewer / ux-critic）はいたが、
「PMOが実際に何をしたか(行動)を監査する担当」がいなかった。
Ratio Guard（Fable版のみ）・ループガード・可視化プロトコルの自己点検は、すべて
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
  "references": { "model-tiering.md": "モデル階層（Fable版はRatio Guardも）" },
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
- **必ず見る既知のドリフト源**（v3.7.2で追加。過去に実際にズレた箇所）:
  1. **v3.8で解消済み**: PMO規律は `agents/jen-pmo.md` が単一の正になった。
     `skills/jen/SKILL.md` は伝言役の定義のみを持つ。SKILL.mdに
     タスク分解・ルーティング表・品質ゲートの記述が**復活していないか**を確認する
     （復活していたら伝言ゲームが再発している）。
  2. `references/model-tiering.md` のモデル表と、各 `agents/*.md` の
     `model:` frontmatter の一致。
  3. コマンド参照の名前空間（Fable版は `/jen:`、Classicは `/jen-classic:`）が
     そのエディションのファイルで正しいか。
  4. `agents/*.md` に登場する全agentが SKILL.md のルーティング表に載っているか
     （`jen-pmo` はメインセッションが担うため委譲先ではない、が既知の例外）。
  5. **散文中のモデルバージョン番号**（v3.8.1で追加）。`model:` は世代
     エイリアスなので自動追随するが、README / SKILL.md / model-tiering.md /
     agent description に書かれた「Opus 5」「Fable 5」等の**説明文は追随しない**。
     v3.8.0時点で旧世代名「Opus 4.8」が10箇所残っていた実績がある。
     現行世代と食い違っていたら `issues` へ挙げる（直すのはPMO/人間）。
- 初回はagents/skills/commands/references配下をフルスキャンして構築する。
  以降は該当ファイルに変更があった時だけ差分更新する（コードマップと同じ方針）。
- **棚卸し対象のパス（重要）**: プラグインとしてインストールされた場合、
  agent/skill/command/referenceファイルの実体は `~/.claude/plugins/cache/...`
  配下にあり、ユーザーのプロジェクトcwdからは `plugins/<plugin>/...` のような
  相対パスでは見えない。**scoutはBashを持たないread-only agentなので
  `$CLAUDE_PLUGIN_ROOT` を自分で解決できない** — 依頼元（PMO、または
  jen-audit実行時のメインセッション）が `echo $CLAUDE_PLUGIN_ROOT` で
  解決した絶対パスを委譲promptに含める。渡されなかった場合、scoutは
  Jenのソースリポジトリ自身を編集している時に限り `plugins/<plugin>/...` の
  相対パスを試し、それも無ければ「未指定のため未実施」と明記して、
  誤った場所を黙ってスキャンしない。
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
| ルーティング記録の整合性 | tool-events.jsonlから読み取れるagent別委譲回数 | routing-stats.jsonの記録件数 | 昇格・委譲の記録漏れ／過少申告（Ratio Guardを持つのはFable版のみ。Classicではルーティング記録の網羅性だけを見る） |
| コンテキストスコープ遵守 | 委譲promptの内容（取得できれば） | — | 「全部読んで」的な指示が残っていないか |
| ループガード遵守 | 同一task_idへの近似委譲の反復回数 | board.md上のSTUCK/昇格記録 | ブレーカーが機能せず同じ手を繰り返していないか |
| **伝言の忠実性（v3.8）** | tool-events.jsonl中のjen-pmo委譲prompt | `.jen/inbox.md` の `[IN-xxx]` 原文 | メインセッションが原文を要約して渡していないか／委譲promptが原文と矛盾していないか |
| **メインセッションの越権（v3.8）** | tool-events.jsonlのAgent呼び出し先 | — | jen-pmo以外へメインセッションが直接委譲していないか（伝言役の逸脱） |

### 判定は3値

- **準拠**: 実ログと自己申告が一致
- **逸脱（証跡付き）**: 実ログの該当行を根拠に不一致を指摘する
- **判定不能（ログ不足）**: ペイロードのスキーマ上、確認できない項目

## 3. 運用ルール

- **強制停止はしない**（v3.4/v3.5/v3.6と同じ理由）。監査は自己点検の一部。
  重大な逸脱（可視化の意図的な隠蔽が疑われる等）はHuman Gate相当として報告する。
- **監査は誰が起動しても良い**。longrunのcheckpoint毎にPMOが依頼するのに
  加えて、`jen-audit` コマンド（Fable版 `/jen:jen-audit` / Classic `/jen-classic:jen-audit`）でユーザーが直接scoutへ依頼できる。
  PMOの自己申告に依存する他の自己点検（ルーティング学習・Ratio Guard等）と違い、
  ユーザー自身が独立に叩けることが、この監査の一番の価値。
- scoutは監査結果を直さない・忖度しない。見つけた不一致をそのまま書く。

## 4. 正直な限界

- haiku・構造的な突き合わせが前提。「PMOの戦略判断が妥当だったか」のような
  価値判断はscoutの仕事ではない（それはverifier/strict-verifier/人間の領分）。
- 監査対象のログ自体（tool-events.jsonl）の記録漏れ・スキーマ不明を
  scoutが検知することはできない（hookの実装依存）。
- PMOがcheckpoint毎の監査依頼自体をサボった場合、それを検知する仕組みは
  ない。ユーザーが `jen-audit` コマンドを直接叩くのが、それに対する唯一の対抗策。
