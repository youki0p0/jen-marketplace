# Copilot Delta — Claude Code 版 Jen からの読み替え（エージェント向け）

この資料は Jen の他の references より**優先する**。他の資料に Claude Code 固有の記述
（`$CLAUDE_PLUGIN_ROOT`・`AskUserQuestion`・`/jen:` 名前空間・`model: fable` など）が
残っていても、ここに書いた読み替えで解釈すること。
制約の根拠と出典は、配布元リポジトリの `copilot/docs/COPILOT_CONSTRAINTS.md` にある。

## 1. 名前と場所

| Claude Code 版 | Copilot 版 |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | リポジトリの `.github/`（解決不要。全員が読める） |
| `${CLAUDE_PLUGIN_ROOT}/hooks/evidence_ledger.py` | `.github/hooks/jen/evidence_ledger.py` |
| `references/*.md` | `.github/skills/jen/references/*.md` |
| `agents/jen-*.md` | `.github/agents/jen-*.agent.md` |
| `/jen:jen-status` 等のコマンド | `/jen-status` 等のスキル |
| ツール `Agent` / `Task` | `agent`（ランタイム名は VS Code Local=`runSubagent`、CLI/Copilot ハーネス=`task`） |
| `Bash` / `Read` / `Write`・`Edit` / `Grep`・`Glob` / `WebSearch`・`WebFetch` | `execute` / `read` / `edit` / `search` / `web` |

**特定のツール名をプロンプトで指示しないこと。** 委譲は「jen-xxx をサブエージェントとして起動」
と書き、ツール名はハーネスに任せる（`runSubagent` は CLI に存在しない）。

## 2. 原文保全はハーネスがやる

`userPromptSubmitted` hook が、`.jen/` が存在するときユーザー入力を `.jen/inbox.md` へ
**逐語で**追記する（見出しに `(captured by hook)`）。

- jen-pmo も worker も inbox を**書かない**。読むだけ。
- 例外: hook を通らない入力（cloud agent への PR コメントでの追加指示、`.jen/` 作成前の最初の入力）
  だけは、受け取ったエージェントが `(manual)` 見出しで逐語追記する。手動経路だと分かるように残す。

## 3. Human Gate

| 面 | やること |
|---|---|
| VS Code / Copilot CLI（jen-pmo がメイン） | 質問ツールが使えるなら**直接ユーザーに聞く**。回答は hook が inbox に入れる |
| jen-pmo が subagent として起動されている | 質問ツールは使えない。**質問文を出力して停止**（Claude 版と同じ） |
| cloud agent | ユーザーがいない。`ask` は deny 扱い。`.jen/human-gate.md` に質問・選択肢・現状を書き、PR 本文にも同じ内容を書いて**停止**する |

人間承認が要る対象は Claude 版と同じ（DB破壊的変更、auth/payment/security境界、secret/env、
本番deploy、外部費用、公開API破壊、大規模リファクタ、法務/価格）。

## 4. モデル階層と昇格

- 各 agent の `model:` はインストール時に `copilot/models.json` から実モデルへ展開済み。
  **Fable 系は組織管理者が有効化しない限り使えない**ため、既定では fable 層を opus に寄せている
  （`install.py --fable` で有効化）。
- **VS Code の制約: メインのモデルより高いコスト帯のモデルは subagent として起動されない。**
  昇格（→ jen-architect / jen-debugger / jen-deep-solver）が拒否されたら、
  それ自体を Human Gate にして「セッションのモデルを上げるか、ここで止めるか」を聞く。
  黙って低いモデルで代行しない。
- CLI は宣言モデルが使えないと**黙ってセッションのモデルに落ちる**。`install.py --surface cli` で
  入れた場合は `modelPolicy: required` で固定してあり、落ちる代わりに起動が拒否される。
- 昇格ラダーは変えない: haiku → sonnet → opus → fable → 人間。

## 5. 並列と隔離

- **worktree 隔離は無い。** Claude 版で `isolation: worktree` だった builder / frontend / test /
  architect / debugger / deep-solver も、同じ作業ツリーを共有する。
  conduct で並列にしてよいのは**触るファイル集合が互いに素なタスクだけ**。迷ったら直列。
- 同時に走れる subagent 数はプランで決まる（CLI: Free 2 / Pro・Pro+ 4 / Max 8 / Business 16 / Enterprise 32）。
  1つの波の幅はこれ以下にする。
- **ネスト**: VS Code Local は既定で subagent からの再委譲が無効（最大5階層）。
  Jen は委譲を jen-pmo だけが行う設計なので、worker に委譲させない（worker の tools に `agent` は無い）。

## 6. 証拠ゲート（v4）の Copilot での動き

- 台帳: `python3 .github/hooks/jen/evidence_ledger.py init|run|attest|revise|status|budget`
- 完了ゲートは `agentStop` hook。全主張 MATCH でないと `decision:"block"` で**もう1ターン強制**される。
- **6回連続で差し戻されると、ゲートは諦めて終了を許す**（CLI が8回で hook を無視するため、その手前）。
  このとき `.jen/logs/stop-events.jsonl` に `gated:false, reason:"block_cap"` が残る。
  行動監査はこれを「ゲート未通過の完了」として数える。差し戻しが続いたら、粘らずに Human Gate へ。
- `.jen/claims.json` は**編集ツールでもシェルでも直接書けない**（preToolUse で拒否）。必ず台帳スクリプト経由。

## 7. 面ごとの欠落

| 機能 | VS Code | CLI | cloud agent |
|---|---|---|---|
| `web`（jen-research の外部調査） | ○ | ○ | **×**（無い。`未確認` として返す） |
| handoffs | Local のみ | × | × |
| hooks | Copilot ハーネスで Preview | ○ | ○（`.github/hooks/*.json` のみ） |
| subagent へのリポジトリ指示の継承 | ○ | **×**（既定） | 未確認 |

CLI の subagent はリポジトリのカスタム指示を既定で受け取らない。
**委譲 prompt に Goal / AC / 教訓ルール / 対象パス / inbox 原文を必ず入れる**
（Jen の「最小コンテキスト委譲」の約束どおり。指示ファイル頼みにしない）。

## 8. cloud agent で longrun するとき

- longrun は cloud agent（`/delegate` や Issue 割当）が向いている。セッションは非対話・権限は事前付与。
- 書けるのは自分の `copilot/*` ブランチ（または指定された PR ブランチ）だけ。`git push` は自分では行わない。
- 環境構築は `.github/workflows/copilot-setup-steps.yml`（ジョブ名 `copilot-setup-steps`、最大59分）。
  Jen の hooks は `python3`（標準ライブラリのみ）しか要らないので、通常は追加不要。
- ネットワークはファイアウォール越し。外部 docs が取れないことを前提に「未確認」を分けて書く。
