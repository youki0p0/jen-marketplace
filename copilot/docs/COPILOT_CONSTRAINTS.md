# GitHub Copilot のエージェント制限・機能制限（Jen 移植のための調査）

調査日: **2026-10-24**。一次情報は `github/docs`（docs.github.com の原稿）と
`microsoft/vscode-docs`（code.visualstudio.com の原稿）の main ブランチ。VS Code 側のページは 2026-10-21 付。
github/awesome-copilot と github.blog の changelog は見ていない。

**「未確認」と書いたものは、文書に記載が見つからなかったか、文書どうしが食い違っていたもの。**
Jen の source-integrity 規則どおり、確定と未確認を混ぜていない。

## 0. 用語の変化（古い記事を読むときの注意）

- **「Copilot coding agent」は「Copilot cloud agent」に改名**されている。
- VS Code のセッションは **ハーネス**（Local / Copilot / Claude / Codex）の上で動く。
  **Copilot ハーネス**は VS Code・CLI・GitHub Copilot app で共通で、エージェント・hook・スキルの形式も CLI と同じ。
  旧来の **Local ハーネス**だけが `runSubagent`・handoffs・prompt files などの独自の慣習を持つ。

## 1. カスタムエージェント（`.agent.md`）

| 項目 | 内容 |
|---|---|
| 置き場所 | リポジトリ `.github/agents/*.agent.md`。組織は `.github`/`.github-private` リポジトリの `agents/`。CLI のユーザー単位は `~/.copilot/agents/`。VS Code は `.claude/agents/*.md` も読む |
| 必須 | `description`（github.com と CLI）。VS Code は全項目任意 |
| 共通の主な項目 | `name` `description` `target`(`vscode`/`github-copilot`) `tools` `model` `disable-model-invocation` `user-invocable` |
| 廃止 | `infer`（→ `disable-model-invocation` と `user-invocable`）。`.chatmode.md` は `.agent.md` へ |
| VS Code のみ | `agents` `argument-hint` `handoffs` `hooks` `reasoning-effort`。`model` は配列可（先頭から使えるもの） |
| CLI のみ | `models`(配列) `modelPolicy`(`preferred`/`required`) `reasoningEffort` `include-custom-instructions`（既定 false） |
| cloud agent が無視 | `argument-hint` `handoffs`。VS Code は `mcp-servers` `metadata` を無視 |
| **本文の上限** | **30,000 文字** |
| 未知のツール名 | 黙って無視される |

## 2. サブエージェント

| | VS Code（Local） | CLI / Copilot ハーネス | cloud agent |
|---|---|---|---|
| 委譲ツール | `runSubagent`（`tools: ['agent']` + `agents: [...]`） | `task` | `agent` 別名（Custom agent ツール） |
| 再委譲（ネスト） | **既定で無効**。`chat.subagents.allowInvocationsFromSubagents` で有効化、最大5階層 | 既定の深さ: **文書内で 4 と 6 が食い違う**（`COPILOT_SUBAGENT_MAX_DEPTH` 既定4 / Subagent limits 表は既定6・最大256）→ 未確認 | 未確認 |
| 同時実行数 | 未確認（例として2並列） | プラン別: Free 2 / Pro・Pro+ 4 / Max 8 / Business 16 / Enterprise 32（最大32） | 未確認 |
| モデル選択 | 明示指定 → agent の `model` → Auto → メインのモデル | 呼び出し時指定 → `~/.copilot/settings.json` の `subagents` → agent の `model`/`models` → 親セッション | ドロップダウンで選ぶ |
| **モデルの制約** | **メインのモデルより高いコスト帯のモデルは subagent として起動されない** | 宣言モデルが使えないと**黙ってセッションのモデルに落ちる**。`modelPolicy: required` なら起動拒否 | 未確認 |
| subagent 内の制約 | 毎回ステートレス。質問ツール・todo は使えない | リポジトリのカスタム指示を既定で受け取らない | — |

## 3. ツール別名（`tools:`、大文字小文字は無視）

| 別名 | 受け付ける旧名 | cloud agent |
|---|---|---|
| `execute` | shell, Bash, powershell | bash/powershell |
| `read` | Read, NotebookRead | view |
| `edit` | Edit, MultiEdit, Write, NotebookEdit | str_replace など |
| `search` | Grep, Glob | search |
| `agent` | custom-agent, Task | custom agent ツール |
| `web` | WebSearch, WebFetch | **無い** |
| `todo` | TodoWrite | **無い** |

`tools` 省略または `["*"]` で全ツール、`[]` で無し。MCP は `server/tool` / `server/*`。

## 4. Agent Skills

- 対応面: cloud agent / code review / CLI / Copilot app / VS Code agent モード。
- 置き場所: `.github/skills/` `.claude/skills/` `.agents/skills/`（個人は `~/.copilot/skills/` など）。
- 必須: `name`（ディレクトリ名と一致・64文字以内）と `description`（1024文字以内）。
- **`name` の文字種: VS Code は小文字・数字・ハイフンのみ。違反すると黙って読み込まれない。**
- 任意: `argument-hint` `user-invocable` `disable-model-invocation`（CLI は `allowed-tools`、VS Code は `context: fork` も）。
- スクリプト等は同じフォルダに置いて相対リンクで参照できる。

## 5. カスタム指示

- リポジトリ全体: `.github/copilot-instructions.md`、または `AGENTS.md`（最も近いもの）、ルートの `CLAUDE.md` / `GEMINI.md`。
- パス別: `.github/instructions/**/*.instructions.md` + `applyTo`。`excludeAgent` で特定エージェントから隠せる。
- **サイズ上限は文書に見当たらない（未確認）。**

## 6. prompt files（`.prompt.md`）

**VS Code の Local ハーネスでしか動かない。** Copilot ハーネス・CLI・cloud agent ではスキルへ変換するよう文書が案内している。
→ Jen のコマンドはスキルとして移植した。

## 7. hooks（Jen の証拠ゲートに直結する部分）

| 項目 | 内容 |
|---|---|
| 置き場所 | リポジトリ `.github/hooks/*.json`、ユーザー `~/.copilot/hooks/`、`.github/copilot/settings(.local).json` の `hooks`、プラグインの `hooks.json`、ポリシー。CLI はリポジトリの `.claude/settings.json` も読む |
| **cloud agent** | **`.github/hooks/*.json` しか読まない**。`bash` か `command` だけを使う |
| VS Code | Copilot ハーネスで Preview。Local ハーネスは別形式（`chat.useHooks`） |
| 形式 | `{"version":1,"hooks":{"<event>":[{"type":"command","bash":"…","powershell":"…","cwd":"…","timeoutSec":30}]}}` |
| イベント | sessionStart / sessionEnd / userPromptSubmitted / userPromptTransformed / preToolUse / postToolUse / postToolUseFailure / agentStop / subagentStart / subagentStop / errorOccurred / preCompact / permissionRequest(CLI) / notification(CLI) |
| ペイロード | camelCase のイベント名 → camelCase の項目（preToolUse は `toolName` `toolArgs`）。PascalCase（`PreToolUse` 等）にすると snake_case と Claude 形式のツール名（`Bash` など）になる |
| ツール拒否 | stdout に `{"permissionDecision":"deny","permissionDecisionReason":"…"}`。cloud agent は `ask` を deny 扱い |
| **preToolUse の故障** | **command 型は fail-closed**（クラッシュ・非ゼロ終了でそのツール呼び出しは拒否） |
| **タイムアウト** | **全イベントで fail-open**（preToolUse・ポリシー hook でもツールは実行される） |
| **agentStop で止める方法** | stdout に `{"decision":"block","reason":"…"}`。**exit 2 は警告扱いで止まらない** |
| 連続 block の上限 | CLI は **8回連続**で hook を無視してターンを終える。入力の `stop_hook_active` で検知できる |
| その他 | postToolUse の `additionalContext` は 10KB まで。hook 出力は 10MiB まで |

## 8. cloud agent の制約

- 環境構築: `.github/workflows/copilot-setup-steps.yml`、ジョブ名は `copilot-setup-steps` の1つだけ、既定ブランチに置く。
  有効な設定は `steps` `permissions` `runs-on` `services` `snapshot` `timeout-minutes`（**最大59**）。
- push 先は新しい `copilot/*` ブランチ（PR で呼ばれたらその PR のブランチ）だけ。自分で `git push` はできない。
- Actions のワークフローは既定で「Approve and run workflows」待ち。
- ファイアウォールが既定で有効（推奨 allowlist + 組織/リポジトリの独自ルール）。
- 非対話の Linux。ツール権限は事前付与。
- 課金はトークン単位の AI credits（旧 premium request の倍率は既存の年額 Pro/Pro+ のみ）。
- **セッションの時間上限・「1タスク1PR」は未確認。**

## 9. Copilot CLI とプラグイン

- `copilot plugin` / `/plugin install|marketplace add|browse`。
- プラグインマニフェストの探索順: `.plugin/plugin.json` → `plugin.json` → `.github/plugin/plugin.json` → **`.claude-plugin/plugin.json`**。
  マーケットプレイスも同様に **`.claude-plugin/marketplace.json`** まで読む。
- `${CLAUDE_PLUGIN_ROOT}` が展開されるのは**エージェントの `mcp-servers` の中だけ**と文書化されている。
  **プラグインの hook コマンドでプラグインルートを参照する方法は未確認。**
- 同名のプロジェクト側エージェント/スキルはプラグイン側を黙って上書きする。
- `/delegate`（または `&` 接頭辞）で cloud agent に渡し、ドラフト PR を作らせる。

## 10. モデル

- CLI の ID: `claude-sonnet-5.5`（既定）`claude-opus-5.5` `claude-haiku-5.5` `claude-haiku-4.5` ほか他社モデル、`auto`。
- **Claude Fable 5 / 5.1 は Copilot で提供されているが、組織管理者が個別に有効化しないと使えない。**
  ZDR の扱いにも条件がある（supported-models）。
- `claude-fable-5.1` という ID、VS Code の `model:` に書く表示名の正確な形式は**未確認**
  （VS Code の handoff の `model` は `名前 (copilot)` 形式と明記されているが、agent の `model` には記載なし）。

---

## 差分マトリクス — Claude Code 版 Jen → Copilot

| Claude Code 版 | Copilot での置き換え | VS Code / cloud agent / CLI | 制約と Jen 側の対処 |
|---|---|---|---|
| スキル `jen`（伝言役） | `.github/skills/jen/SKILL.md` | ○ / ○ / ○ | **jen-pmo を直接選ぶのを標準に変更**（下記の理由） |
| `jen-pmo` subagent（唯一の指揮） | `.github/agents/jen-pmo.agent.md`（`user-invocable: true`） | ○ / ○ / ○ | VS Code は subagent のモデルがメイン以下に縛られ、再委譲も既定で無効 → PMO をメインに置く |
| 17体の worker | `.github/agents/jen-*.agent.md`（`user-invocable: false`） | ○ / ○ / ○ | 本文 ≤30,000 文字（最大の jen-pmo でも余裕あり） |
| `model: haiku/sonnet/opus/fable` | `copilot/models.json` で実モデル名に展開 | ○ / ○ / ○ | Fable は組織での有効化が必要 → 既定は opus に寄せる。`--fable` で有効化 |
| AXIOM-0（判断は Claude のみ） | 全 agent の `model` を Claude 系に固定 | 表示のみ / 表示のみ / **`modelPolicy: required` で強制** | VS Code と cloud agent はユーザーがモデルを変えられる（強制手段なし） |
| `isolation: worktree` | **無い** | ✗ / ✗ / ✗ | 並列は触るファイルが互いに素なタスクだけ。worker 本文に注記 |
| 並列ファンアウト | subagent の並列 | 未確認 / 未確認 / プラン別上限 | 波の幅を同時実行数以下に |
| `AskUserQuestion` 剥奪 → 伝言役が Human Gate を仲介 | メインの PMO が直接質問 | ○ / **✗（ユーザー不在）** / ○ | cloud agent は `.jen/human-gate.md` と PR 本文に書いて停止 |
| 伝言役 LLM が `.jen/inbox.md` へ逐語保存 | **`userPromptSubmitted` hook が保存** | Preview / 初回のみ / ○ | LLM のお願いから決定論へ格上げ。`.jen/` がある時だけ（opt-in） |
| PreToolUse（危険コマンド拒否） | `preToolUse` + `copilot_pre_tool_guard.py` | Preview / ○ / ○ | 拒否パターンは Claude 版と共有。**編集ツールでの台帳書き換えも拒否**（Claude 版より強い）。内部故障は「判断なし」に倒す（fail-closed で全ツールが止まるのを避ける） |
| PostToolUse（実ログ） | `postToolUse` + `copilot_post_tool_log.py` | Preview / ○ / ○ | `.jen/` が無ければ書かない。ツール結果本文は 2000 文字で切る |
| Stop（exit 2 で差し戻し） | `agentStop` + `copilot_stop_gate.py`（`decision:"block"`） | Preview / ○ / ○ | exit 2 では止まらないので JSON に翻訳。**6回連続で諦めて `block_cap` を記録**（CLI 上限8の手前） |
| `/jen:jen-status` 等のコマンド | スキル `/jen-status` 等 | ○ / △（ユーザー起動なし） / ○ | prompt files は Local 限定なのでスキルを選んだ |
| `CLAUDE_PLUGIN_ROOT` | リポジトリの `.github/` | — | パスはインストール時に書き換え。scout の棚卸し対象も `.github/` 固定 |
| WebSearch / WebFetch（research, deep-solver, pmo） | `web` | ○ / **✗** / ○ | cloud agent では外部調査不可 → 「未確認」で返す |
| プラグイン配布 | 対象リポジトリへの展開（`copilot/install.py`） | — | プラグイン hook のルート参照方法が未確認、cloud agent はプラグイン hook を読まない → **リポジトリ展開を正式経路にした** |
| longrun（多日自走） | cloud agent（`/delegate` / Issue 割当） | — / ○ / `/delegate` | setup ジョブ ≤59分。強制ターンもジョブ時間に数えられる |

## 出典

- https://docs.github.com/en/copilot/reference/custom-agents-configuration
- https://docs.github.com/en/copilot/reference/hooks-reference
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference
- https://docs.github.com/en/copilot/reference/ai-models/supported-models
- https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference
- https://code.visualstudio.com/docs/agents/run/subagents
- https://code.visualstudio.com/docs/agent-customization/agent-skills
- https://code.visualstudio.com/docs/agent-customization/hooks
- https://code.visualstudio.com/docs/agent-customization/migrate-customizations
- https://code.visualstudio.com/docs/agent-customization/prompt-files
- https://code.visualstudio.com/docs/agent-customization/custom-instructions
- github/docs: `how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/customize-the-agent-environment.md`、
  `concepts/security-governance-and-network-settings/risks-and-mitigations.md`、`customize-the-firewall.md`、
  `add-repository-instructions.md`、`reference/copilot-billing/models-and-pricing.md`
