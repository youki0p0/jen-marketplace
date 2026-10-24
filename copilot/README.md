# Jen for GitHub Copilot 🎼

**完了は、証拠で決める。** Claude Code 版 Jen（PMO型オーケストレーター）の考え方を、
GitHub Copilot（VS Code / Copilot CLI / cloud agent）で動く形に移したもの。

中身は Claude Code 版と**同じ原典**から作る。`install.py` が `plugins/jen`（または `plugins/jen-classic`）を
読み、Copilot の形式に変換して、あなたのリポジトリの `.github/` へ展開する。
Copilot 用のファイルを別に持たないので、Claude 版を直せば Copilot 版も同じになる。

> 対象は Copilot の**2026-10 時点の仕様**。調べた制約と出典、未確認の点は
> [docs/COPILOT_CONSTRAINTS.md](docs/COPILOT_CONSTRAINTS.md) にある。

## 何が同じで、何が変わったか

**同じ**: 18体の役割分担（PMO・scout・builder・verifier…）、受入条件と Task Ledger、
昇格ラダー（haiku → sonnet → opus → fable → 人間）、Human Gate、教訓台帳、ループガード、
そして v4 の**証拠ゲート**（全主張が MATCH になるまで完了を差し戻す。判定ロジックは Claude 版の hooks をそのまま使う）。

**変わった**（Copilot の制約に合わせた）:

| | Claude Code 版 | Copilot 版 | なぜ |
|---|---|---|---|
| 入口 | メインセッションは伝言役、jen-pmo は subagent | **jen-pmo を直接選ぶ** | VS Code は subagent のモデルがメインのモデル以下に縛られ、subagent からの再委譲も既定で無効 |
| 原文保全 | 伝言役の LLM が `.jen/inbox.md` へ逐語追記 | **`userPromptSubmitted` hook が追記** | LLM への「お願い」から決定論へ。言い換えが構造的に起きない |
| Human Gate | 伝言役が質問を仲介 | PMO が直接聞く／cloud agent は `.jen/human-gate.md` と PR に書いて停止 | cloud agent にはユーザーがいない |
| 完了ゲート | Stop hook が exit 2 | `agentStop` hook が `{"decision":"block"}` | Copilot では exit 2 で止まらない |
| 差し戻しの上限 | なし | **6回連続で諦め、`block_cap` を記録** | CLI は8回連続 block で hook を無視する。黙って突破されるより先に、記録付きで止める |
| 台帳の保護 | シェル経由の書き換えを拒否 | **編集ツール経由も拒否** | Copilot の編集ツールは台帳を直接書ける |
| 並列 | worker は worktree で隔離 | 隔離なし。**触るファイルが互いに素なときだけ並列** | Copilot に worktree 隔離が無い |
| モデル | `fable/opus/sonnet/haiku` エイリアス | `models.json` で実モデル名に展開。既定で fable → opus | Fable は組織の管理者が有効化しないと使えない |
| コマンド | `/jen:jen-status` など | スキル `/jen-status` など | prompt files は VS Code の Local ハーネスでしか動かない |

## インストール

必要なもの: Python 3.10+（対象マシンと cloud agent の両方。hooks は標準ライブラリのみ）。

```bash
git clone https://github.com/youki0p0/jen-marketplace
cd your-repo
python3 ../jen-marketplace/copilot/install.py --target . --gitignore
git add .github .gitignore && git commit -m "Add Jen for Copilot"
mkdir .jen   # 任意: 最初の入力から hook に原文を保存させる
```

`--gitignore` は `.jen/` を `.gitignore` に追記する。**`.jen/logs/` にはツールの引数が平文で残る**ので、必ず除外すること。

### オプション

| オプション | 意味 |
|---|---|
| `--edition jen-classic` | Lean 版（単一で回し、委譲はコンテキスト劣化時だけ。Fable 不要） |
| `--surface portable` | 既定。モデル ID のみ書く（cloud agent / CLI / VS Code 共通） |
| `--surface cli` | CLI 向け。`modelPolicy: required` で**宣言外のモデルへ黙って落ちない**（AXIOM-0 を機械で守る） |
| `--surface vscode` | VS Code 向け。表示名＋`reasoning-effort` |
| `--fable` | fable 層（jen-pmo / jen-deep-solver）を Fable で動かす。組織での有効化が必要 |
| `--no-instructions` | `.github/instructions/jen.instructions.md` を入れない |
| `--dry-run` | 書き込まずに計画だけ表示 |
| `--force` | 手で変更したファイルも上書き／削除する |
| `--uninstall` | 入れたものを外す（手で変更したファイルと `.jen/` は残す） |

再実行すると更新になる。前回入れたまま手を入れていないファイルだけを上書きし、
手で変えたファイルや Jen 以外のファイルとぶつかったら止まる（`.github/jen-copilot.lock.json` で判定）。

## 使い方

**エージェント一覧から `jen-pmo` を選んで**、ゴールを渡す。

- **VS Code**: チャットのエージェントピッカーで `jen-pmo`
- **Copilot CLI**: `copilot --agent jen-pmo`（または `/agent`）
- **cloud agent**: Issue を Copilot に割り当てるとき、カスタムエージェント `jen-pmo` を選ぶ。CLI からは `/delegate`

```
conduct
Goal: サインアップ後のオンボーディング画面を改善し、
      初回ユーザーが3分以内に主要機能へ到達できるようにする。
Must Have: 既存デザイントークン準拠 / モバイル対応 / 既存テストを壊さない
Out of Scope: 課金導線の変更 / DB schema 変更
Acceptance Criteria:
- 初回画面に次アクションが表示される
- lint / typecheck / test が通る
```

別のエージェントから `/jen <goal>` でも呼べるが、そのときは jen-pmo が subagent になり、上の制約を受ける。

| モード | 用途 |
|---|---|
| `route` | 小タスク。1工程ずつ振って verifier 合格まで |
| `conduct` | 中〜大規模。DAG 分解し、触るファイルが重ならない工程だけ並列 |
| `repair` | 失敗・バグの切り分け → 最小修正 → 回帰 → 検収 |
| `review` | UX / セキュリティ / 反対意見 / 収益化レビュー |
| `release` | PR 要約・検証パケット・ロールバック。deploy は人間承認で停止 |
| `longrun` | チェックポイントと品質ゲートを挟み完了まで。cloud agent 向き |

スキル: `/jen-status` `/jen-board` `/jen-standup` `/jen-pr` `/jen-audit` `/jen-review` `/jen-repair` `/jen-release` `/jen-longrun`

## 面ごとの対応状況

| | VS Code | Copilot CLI | cloud agent |
|---|---|---|---|
| エージェント・スキル | ○ | ○ | ○ |
| hooks（原文保全・ガード・証拠ゲート） | ○（Copilot ハーネス。**Preview**） | ○ | ○ |
| Human Gate で直接質問 | ○ | ○ | ✗ → ファイルと PR に書いて停止 |
| 外部 web 調査（jen-research） | ○ | ○ | ✗ |
| モデルの強制（AXIOM-0） | ✗（表示のみ） | ○（`--surface cli`） | ✗ |
| 長時間の自走 | △ | △ | ○ |

VS Code の **Local ハーネス**は hooks の入出力形式が違い、このキットでは検証していない。Copilot ハーネスで使うこと。

## 正直な限界

- **実機では未検証。** 変換結果とアダプタは試験で固めてある（`tests/test_copilot_port.py`。
  Copilot の文書にあるペイロード形式を入力して確認）が、実際の VS Code / CLI / cloud agent での
  エンドツーエンドの動作確認はしていない。導入したら最初に小さなゴールで、jen-pmo が jen-scout へ
  委譲できること・`.jen/inbox.md` に原文が入ること・未被覆で終わろうとすると差し戻されることを確かめてほしい。
- **モデル名**: `claude-fable-5.1` の ID と、VS Code 形式の表示名は推定。違ったら `copilot/models.json` を直して再インストール。
- **タイムアウトはガードを素通りさせる。** Copilot の hook はタイムアウトすると常に fail-open。
  ガードは軽い正規表現だけにしてあるが、これを安全境界とは見なさないこと（Claude 版と同じく「カジュアルな事故を塞ぐ」まで）。
- **ガードの内部故障は「判断なし」に倒している。** Copilot の preToolUse は落ちると拒否になるので、
  ガードのバグで全ツールが止まるのを避けた。故障は `.jen/logs/guard-errors.jsonl` に残る。
- **完了ゲートは6回で諦める。** CLI の8回上限で黙って無視されるより、記録して止める方を選んだ。
  `/jen-audit` が「ゲート未通過の完了」として数える。
- **プラグイン配布は未対応。** Copilot CLI は `.claude-plugin/` を読めるが、プラグインの hook から
  プラグインのルートを参照する方法が文書で確認できず、cloud agent はプラグインの hook を読まない。
  そのためリポジトリへの展開を正式経路にした。

## 構成

```
copilot/
├─ install.py            原典を読んで変換・展開する（標準ライブラリのみ）
├─ models.json           階層 → 実モデル名の対応（世代が変わったらここだけ直す）
├─ kit/                  Copilot 固有の差分だけ
│  ├─ hooks/             jen.json と 4つのアダプタ（inbox / guard / post-log / stop-gate）
│  ├─ agents/            jen-pmo・jen-scout の先頭に足す読み替え
│  ├─ skills/jen/        入口スキル（Copilot 用に書き直し）
│  ├─ references/        copilot-delta.md（エージェント向けの読み替え規則）
│  └─ instructions/      .jen/** を触るときの規則
└─ docs/COPILOT_CONSTRAINTS.md   調査結果と出典
```
