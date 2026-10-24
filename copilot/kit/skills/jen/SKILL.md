---
name: jen
description: Jen v4 PMO型AI開発オーケストレーター（GitHub Copilot版）。ゴールだけを渡されたとき、route/conduct/repair/review/release/longrunでタスクを分解し、jen-* カスタムエージェントへ委譲し、受入条件・証拠ゲート・検収・差し戻し・昇格・handoffまで管理する。Jen/Jenny/ジェン/ジェニー/ジェニファー、PMO、オーケストレーション、自走、検証、差し戻し、DAG、長時間開発の依頼で使う。Jen自身の能力（使えるエージェント・スキル一覧）を尋ねる質問でも使う。
argument-hint: "[route|conduct|repair|review|release|longrun] <goal>"
---

# Jen for GitHub Copilot — 入口

**オーケストレーションは `jen-pmo` カスタムエージェントだけが行う。**
このスキルを読んだあなたの仕事は、ユーザーの言葉を**一字一句そのまま** jen-pmo へ届けることだけ。

## いちばん良い使い方（推奨）

エージェント一覧から **`jen-pmo` を直接選んで**ゴールを渡す。

- VS Code: エージェントピッカーで `jen-pmo` を選ぶ
- Copilot CLI: `copilot --agent jen-pmo` または `/agent` で選ぶ
- cloud agent（github.com）: Issue を Copilot に割り当てるときカスタムエージェント `jen-pmo` を選ぶ

理由は2つある（Claude Code 版との最大の違い）:

1. **VS Code では、メインのモデルより高いコスト帯のモデルを subagent として起動できない。**
   jen-pmo を subagent として呼ぶと、その時点のセッションモデル以下に縛られる。
   jen-pmo をメインにすれば、指揮層のモデルがそのまま使える。
2. **メインのエージェントはユーザーに直接質問できる**（cloud agent を除く）。
   Claude Code 版の「伝言役のメインセッション」が要らなくなる。
3. **VS Code の Local ハーネスは subagent からの再委譲が既定で無効**
   （`chat.subagents.allowInvocationsFromSubagents`）。jen-pmo を subagent として呼ぶと、
   jen-pmo が worker へ委譲できない。

## このスキル経由で呼ばれた場合（jen-pmo 以外のエージェントで `/jen` された）

1. `.jen/` が無ければ作る: `mkdir -p .jen/logs .jen/reports .jen/checkpoints`
2. `.jen/inbox.md` を確認する。`userPromptSubmitted` hook は **`.jen/` が既にあるときだけ**
   原文を保存するので、**最初の1回だけは保存されていない**。今回の入力が無ければ、
   `## [IN-xxx] <ISO時刻>  (manual)` 見出しで**一字一句そのまま**追記する（要約・整形・翻訳しない）。
3. `jen-pmo` を subagent として起動し、その原文を**丸ごと**渡す。モード指定もそのまま。
4. jen-pmo の出力をそのまま返す。勝手に要約しない。
5. subagent の起動がモデルのコスト帯で拒否された場合は、自分で PMO を代行せず
   「エージェントピッカーで jen-pmo を選んで同じ文を送ってほしい」とユーザーへ伝える。

### やってはいけないこと

- タスク分解 / 受入条件の作成 / DAG化 / 品質ゲート判断（jen-pmo の仕事）
- worker（jen-builder / jen-test / jen-verifier …）への**直接**委譲
- ユーザー入力を言い換えて渡すこと（最大の禁止事項）

## 状態ファイルと道具の場所（Copilot 版の配置）

| もの | 場所 |
|---|---|
| 実行時の状態 | `.jen/`（gitignore すること） |
| 証拠台帳スクリプト | `.github/hooks/jen/evidence_ledger.py` |
| hooks 定義 | `.github/hooks/jen.json` |
| エージェント | `.github/agents/jen-*.agent.md` |
| 参照資料 | `.github/skills/jen/references/` |
| Copilot 固有の差分 | `.github/skills/jen/references/copilot-delta.md` |

## 参照

- Copilot 版の制約と読み替え: `references/copilot-delta.md`（**最初に読む**）
- 伝言役プロトコル（Claude 版の原典）: `references/relay-protocol.md`
- PMO の全プロトコル: `.github/agents/jen-pmo.agent.md`
