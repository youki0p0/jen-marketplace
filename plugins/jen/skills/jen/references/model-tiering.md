# Jen v3 Model Tiering — Fable-Orchestrator Topology

## 基本トポロジー

v3 の核は「**指揮は Fable、実行は安いモデル**」。
オーケストレーション（分解・順序付け・結果の判定・長時間の一貫性維持）は
Claude Fable 5 の長所そのものであり、実装・調査などの手足は sonnet / haiku で足りる。

| 層 | agent | model | 理由 |
|---|---|---|---|
| 指揮 | jen-pmo | fable | 長時間の計画維持・委譲・自己検証が主戦場 |
| 設計 | jen-architect | fable | 設計はトークン軽量かつ下流への影響が最大。上流に最高知能を置く |
| 軽作業 | jen-scout | haiku | 下調べ・要約 |
| 標準実行 | builder / frontend / test / research / reviewers | sonnet | 実装・QA・レビューの主力 |
| 上位実行 | debugger / strict-verifier | opus | 不明バグ・高リスク検収 |
| 最終昇格 | jen-deep-solver | fable | 上位層が失敗した問題のみ |

## Escalation Ladder

```
haiku → sonnet → opus → fable (jen-deep-solver)
```

- verifier REJECT 1回 → 同担当へ差し戻し
- verifier REJECT 2回 → 上位層（architect / debugger）へ昇格
- 上位層が失敗、または REJECT 3回 → **jen-deep-solver（fable）** へ昇格
- deep-solver でも解けない → Human Gate（人間へ返す）

## コスト規律

- Fable 5 の API 単価は Opus 4.8 の約2倍。サブスク利用でも消費が速い。
- したがって Fable を使うのは **PMO・architect・deep-solver の3箇所だけ**。
- architect が fable なのは例外ではなく同じ原則の適用:
  「トークンを大量に消費する層（実装・探索）は安く、判断が下流全体を規定する層は賢く」。
  設計の1ターンは実装よりはるかに軽く、設計ミスは「実装→REJECT→再実装」ループで
  sonnet/opus のトークンを最も高く燃やす。
- architect は自分で重い実装を抱え込まない。設計を添えて builder へ返す。
- PMO は自分で実装・探索しない（v2 から継続の最重要ルール）。Fable の PMO が
  手を動かし始めるとコストとコンテキストが同時に汚れる。

## デザインの正本は Claude Design

視覚デザイン・デザインシステムの管理はエージェントに発明させず、
**Claude Design（claude.ai/design）** に寄せる。

- デザインシステムプロジェクトを正本とし、`/design-sync` でローカルの
  コンポーネントライブラリへ同期する（同期はメインセッション/人間が行う）。
- jen-frontend は同期済みライブラリに従って実装に徹し、デザインを発明しない。
- jen-ux-critic は「正本との一致」を検収基準に含める。
- 正本にないコンポーネントが必要になったら、Jen 側で捏造せず
  「Design 側の更新が必要」として PMO → 人間へ返す。

## 運用上の注意（実測ベースの落とし穴）

1. **メインセッションを Fable にする**: `/model fable`。Claude Code v2.1.170 以降が必要
   （古い場合は `claude update`）。
2. **`CLAUDE_CODE_SUBAGENT_MODEL` を確認**: この環境変数が設定されていると、
   agents の frontmatter `model:` 指定を上書きし、fable 指定の agent が別モデルで
   静かに動く。`unset CLAUDE_CODE_SUBAGENT_MODEL` するか `inherit` を外す。
3. **classifier フォールバック**: 高リスク領域に触れるとセッションが Opus 4.8 へ
   ルーティングされ、そのまま Opus で継続することがある。longrun 中にこれを検知したら
   handoff を更新して新セッションで再開する（longrun-playbook 参照）。
4. **thinking は常時 ON**: Fable 5 は adaptive thinking を無効化できない。
   effort で調整する（PMO / deep-solver は max、それ以外は agent 定義に従う）。

## nested subagents

Claude Code は subagent がさらに subagent を起動できる。v3 では以下のみ許可する:

- 許可: builder / architect / debugger が **自分専用の scout（haiku）** を起動して
  read-only 探索を任せる。
- 禁止: specialist が別の実装系 agent を起動する（責任境界と Task Ledger が壊れる）。
  実装の再委譲が必要なら PMO へ返す。
