# Jen Classic Model Tiering — Opus-Orchestrator Topology

## 基本トポロジー（Fable不使用）

| 層 | agent | model | 備考 |
|---|---|---|---|
| 指揮 | jen-pmo | opus | Fable版との差は「構造補償」で埋める（下記） |
| 軽作業 | jen-scout | haiku | |
| 標準実行 | builder / frontend / test / research / reviewers | sonnet | |
| 上位実行 | architect / debugger / strict-verifier | opus | |
| 最終昇格 | jen-deep-solver | opus + 合議制 | 単独fableの代替（下記） |

メインセッションは v3.8 で**伝言役**になったため、PMOを兼ねない。
PMOは `jen-pmo` subagent（frontmatterで `model: opus` 固定、セッションのモデルとは独立）。
したがってメインセッションのモデルはコスト削減の余地になったが、
伝言役に求められるのは「原文を要約しない」指示追従の忠実性なので極端に安いモデルは避ける。

### モデル指定は世代エイリアス（v3.8.1で明文化）

上表・各 `agents/*.md` の `model:` は **`opus` / `sonnet` / `haiku` の
エイリアス**（Classicは `fable` を使わない）であり、`claude-opus-5` のような
特定バージョンIDを固定していない。
したがって Claude 側の世代が上がれば、Jen 側を書き換えなくても各層は
**自動的に最新世代へ解決される**。

- ドキュメント本文にバージョン番号（「Opus 5」等）が出てくるのは
  **説明のための例示**であって、動作を決めているのはエイリアスの方である。
- 逆に言えば、本文のバージョン番号は放置すると古くなる。skillmap 整合性
  チェック（behavior-audit.md）の「既知のドリフト源」として扱い、
  世代が変わったら本文側を追随させる。
- 特定バージョンへ固定したい場合のみ、`model:` にモデルIDを直接書く
  （その時点で自動追随はしなくなる）。
- 執筆時点の解決先: opus=Claude Opus 5 / sonnet=Claude Sonnet 5 /
  haiku=Claude Haiku 4.5。

## Fableとの差分と構造補償

Fableの長所（長時間の計画維持・ドリフト耐性）をモデルで持てないぶん、以下で補う:

1. **再アンカリング（毎委譲）**: PMOは委譲のたびに `.jen/mission.md` の
   Goal / Non-goals / AC を読み直してから指示を書く。記憶に頼らない。
2. **サイクル短縮**: longrunの1サイクルは「タスク1つ」を厳守。
   まとめ処理はドリフトの温床。
3. **セッションローテーション**: 8サイクル毎、またはコンテキスト圧迫・
   応答品質低下を感じたら、handoff.md を更新して新セッションで再開する。
   Fable版の「回し続けてよい」はClassicでは適用しない。
4. **opus合議制（deep-solver）**: fable単独の代わりに、
   architect と debugger に独立で仮説を出させ（並列・互いの出力を見せない）、
   deep-solver(opus) が両仮説と失敗履歴を統合して最終解を出す。
   独立仮説の突き合わせで、単独モデルの思い込みを相殺する。

## Escalation Ladder（Classic）

```
haiku → sonnet → opus → opus合議(jen-deep-solver) → Human Gate
```

- verifier REJECT 2回 → opus層（architect / debugger）へ昇格
- REJECT 3回 or opus層失敗 → 合議制: architect+debugger 独立仮説 →
  jen-deep-solver が統合。失敗履歴（タイプタグ付き）を全員に配布
- 合議でも解けない → Human Gate

## コスト特性

- Opus 5 は Fable 5 の約半額。合議制（opus×3呼び出し）を使っても
  fable単独昇格とほぼ同等のコストに収まる。
- PMO委譲規律（自分で実装しない）はClassicでも最重要。変更なし。

## 運用上の注意

- `CLAUDE_CODE_SUBAGENT_MODEL` は未設定に（Fable版と同じ罠）。
- jen（Fable版）と jen-classic を**同時に有効化しない**こと。
  agent名が同一のため競合する。切り替えは片方を disable してから。

## subagent の委譲権限（v3.8で訂正）

`tools:` は**許可リスト**であり、`Agent`（サブエージェント起動ツール。旧称 Task）を
明記していない agent は**構造的に委譲できない**。

- **委譲できるのは `jen-pmo` だけ**（`tools:` に `Agent` を持つ唯一の agent）。
- worker は `Agent` を持たないため、探索が必要でも**PMOへ差し戻す**。
- v3.7以前の「builder/architect/debugger が自分専用の scout を起動してよい」は
  実現不能な記述だったため撤回した。

> ⚠️ 未検証: インタラクティブセッションではサブエージェントが background 実行になり、
> `Agent` が保持されるか公式ドキュメントの記述が競合している。
> 回避策は `references/relay-protocol.md`「前提条件」を参照。
