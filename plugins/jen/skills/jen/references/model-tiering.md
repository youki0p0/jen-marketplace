# Jen v3 Model Tiering — Fable-Orchestrator Topology

## 基本トポロジー

v3 の核は「**指揮は Fable、実行は安いモデル**」。
オーケストレーション（分解・順序付け・結果の判定・長時間の一貫性維持）は
Claude Fable 5 の長所そのものであり、実装・調査などの手足は sonnet / haiku で足りる。

| 層 | agent | model | 理由 |
|---|---|---|---|
| 指揮 | jen-pmo | fable | 長時間の計画維持・委譲・自己検証が主戦場 |
| 軽作業 | jen-scout | haiku | 下調べ・要約 |
| 標準実行 | builder / frontend / test / research / reviewers | sonnet | 実装・QA・レビューの主力 |
| 上位実行 | architect / debugger / strict-verifier | opus | 難設計・不明バグ・高リスク検収 |
| 最終昇格 | jen-deep-solver | fable | opus 層が失敗した問題のみ |

### モデル指定は世代エイリアス（v3.8.1で明文化）

上表・各 `agents/*.md` の `model:` は **`fable` / `opus` / `sonnet` / `haiku` の
エイリアス**であり、`claude-opus-5` のような特定バージョンIDを固定していない。
したがって Claude 側の世代が上がれば、Jen 側を書き換えなくても各層は
**自動的に最新世代へ解決される**。

- ドキュメント本文にバージョン番号（「Opus 5」等）が出てくるのは
  **説明のための例示**であって、動作を決めているのはエイリアスの方である。
- 逆に言えば、本文のバージョン番号は放置すると古くなる。skillmap 整合性
  チェック（behavior-audit.md）の「既知のドリフト源」として扱い、
  世代が変わったら本文側を追随させる。
- 特定バージョンへ固定したい場合のみ、`model:` にモデルIDを直接書く
  （その時点で自動追随はしなくなる）。
- 執筆時点の解決先: fable=Claude Fable 5 / opus=Claude Opus 5 /
  sonnet=Claude Sonnet 5 / haiku=Claude Haiku 4.5。

### architect は opus のまま（検討したが不採用）

「設計はトークン軽量・下流影響最大だから fable にすべき」という案を検討したが、
実測比率（下記「目標分布」）と整合しないため不採用とした。architect は
「難所だけ」とはいえ deep-solver（真の最終手段）より高頻度で発火するため、
fable へ動かすと fable の呼び出しシェアが目標の約4%から2倍以上に膨らみ、
単価差（fable は opus の約2倍）がそのままコスト増に直結する。
上位実行3体（architect/debugger/strict-verifier）を opus に揃えたまま
呼び出し頻度で自然に絞る方が、実測で「バランスがいい」比率を再現できる。

## Escalation Ladder

```
haiku → sonnet → opus → fable (jen-deep-solver)
```

- verifier REJECT 1回 → 同担当へ差し戻し
- verifier REJECT 2回 → opus 層（architect / debugger）へ昇格
- opus 層が失敗、または REJECT 3回 → **jen-deep-solver（fable）** へ昇格
- deep-solver でも解けない → Human Gate（人間へ返す）

## コスト規律

- Fable 5 の API 単価は Opus 5 の約2倍。サブスク利用でも消費が速い。
- したがって Fable を使うのは **PMO と deep-solver の2箇所だけ**。
- PMO は自分で実装・探索しない（v2 から継続の最重要ルール）。Fable の PMO が
  手を動かし始めるとコストとコンテキストが同時に汚れる。

## 目標分布（v3.5、実測ベース）

手動運用での体感から得られた呼び出し比率 **sonnet : opus : fable ≈ 20 : 4 : 1**
（呼び出し数シェアで sonnet 80% / opus 16% / fable 4%）を、この設計が
狙っている分布として明文化する。厳密な割当ノルマではなく、
「今の担当×モデル構成が続く限り自然にこの近辺へ収束するはず」という
健全性チェックの基準値。

参考: 単価差込みのコスト内訳（出力寄り加重の概算）は
sonnet 約57% / opus 約29% / fable 約14%。呼び出し数では少数派の
opus/fable が、単価の高さでコストシェアを押し上げる形が想定どおり。

> **v3.8.1 で引き直した**: v3.5〜v3.8 は Sonnet 4系（$3/$15）前提で
> 「sonnet 約67% / opus 約22% / fable 約11%」と記載していた。Sonnet 5 は
> $2/$10 なので上記へ更新した。**呼び出し比率 20:4:1 は変えていない** —
> sonnet が相対的に安くなった分、同じ呼び出し構成でもコストが上位層へ
> 寄っただけである。判断の目安（下記）は呼び出し数ベースなので影響を受けない。

## Ratio Guard（比率監視）

自己改善ループ（v3.1）が書く `.jen/routing-stats.json` から実測比率を出す。
強制停止はしない（v3.4の不変条件どおり、数値によるhard-stop自動化はしない）。
PMOへの自己点検シグナルとして扱う。

### ⚠️ 測定できるものと、できないもの（v3.7.2で訂正）

`routing-stats.json` は**1タスク完了につき1行**、その**委譲先agentのmodel**を
記録する。したがって:

- **PMO(fable)は行にならない** — PMOは委譲「元」であり委譲先ではないため。
- よって統計上の `fable` 行は実質 **deep-solver のみ**。
- つまりこの統計は上記「目標分布」（指揮を含む全体の呼び出し比率）を
  **測っていない**。測れるのは「**委譲先の分布**」だけである。

v3.5では両者を同一視して「opus:fable ≈ 4:1 が健全」と書いていたが、これは誤り。
委譲先ベースで opus:fable = 4:1 は「opusタスク4件につき1件deep-solverが発火」
＝最終手段が常用されている異常事態を意味する。以下に訂正する。

### 判断の目安（委譲先ベース）

- `/jen:jen-status` が `.jen/routing-stats.json` を集計して表示する
  （`jen_status.py` 参照）。
- **sonnet:opus の目安は 5:1**（目標分布と整合する唯一の指標）。
  3:1を下回ったら「本来sonnetで済む案件をopusへ昇格しすぎていないか」を
  点検し、REJECT基準（2回で昇格）を守れているか確認する。
  8:1を上回るのは単に難所が少なかっただけで悪い兆候ではない。
- **deep-solver(fable)は「稀であるほど健全」**。目標値は設けない。
  opus:fable が **10:1 を下回ったら要注意、4:1 を下回ったら異常**として
  「opus層がなぜ繰り返し失敗しているか」「classifierフォールバックで
  opus層がfable相当のコストを静かに食っていないか」（運用上の注意 #3）を
  点検し、`.jen/decisions.md` に一行残す。
- **指揮側(PMO/fable)の消費は本統計では測れない**。知りたい場合は
  Claude Code側の使用量表示など、Jenの外側の手段で確認すること。
- longrun の checkpoint 毎、または conduct/route で20タスク処理毎に
  自己点検する（routing-policy.md参照）。

## 運用上の注意（実測ベースの落とし穴）

1. **メインセッションのモデル（v3.8で意味が変わった）**: v3.7までは
   メインセッション自身がPMOだったため `/model fable` が必須だった。
   v3.8ではメインセッションは**伝言役**であり、PMOは `jen-pmo` subagent
   （frontmatterで `model: fable` 固定、セッションのモデルとは独立）が担う。
   したがってメインセッションを fable にする必然性は無くなり、**コスト削減の
   余地になった**。ただし伝言役に求められるのは「原文を絶対に要約しない」という
   指示追従の忠実性そのものなので、極端に安いモデルは避ける。
   Claude Code v2.1.170 以降が必要（古い場合は `claude update`）。
2. **`CLAUDE_CODE_SUBAGENT_MODEL` を確認**: この環境変数が設定されていると、
   agents の frontmatter `model:` 指定を上書きし、fable 指定の agent が別モデルで
   静かに動く。`unset CLAUDE_CODE_SUBAGENT_MODEL` するか `inherit` を外す。
3. **classifier フォールバック**: 高リスク領域に触れるとセッションが Opus 5 へ
   ルーティングされ、そのまま Opus で継続することがある。longrun 中にこれを検知したら
   handoff を更新して新セッションで再開する（longrun-playbook 参照）。
4. **thinking は常時 ON**: Fable 5 は adaptive thinking を無効化できない。
   effort で調整する（PMO / deep-solver は max、それ以外は agent 定義に従う）。
5. **agent frontmatter のキー（v3.8で調査結果を反映）**:
   公式にサポートが確認できたもの — `name` / `description` / `tools`（許可リスト）/
   `model` / `memory`（`user`｜`project`｜`local`）/ `background`。
   **未確認** — `effort` / `isolation` / `color`。
   無視されている場合、`isolation: worktree`（6 agents）はワークツリー分離を
   しておらず、`effort: max` も効いていない可能性がある。
   **分離を前提にした安全設計（並列実行で同じファイルを触る等）はしないこと** —
   並列化の可否は routing-policy.md の条件で判断する。
6. **`tools:` を書いた時点で許可リストになる**。省略すれば継承だが、Jenは全agentで
   明記しているため、書いていないツールは使えない。`Agent`（委譲）を持つのは
   `jen-pmo` のみ（下記「subagent の委譲権限」）。

## subagent の委譲権限（v3.8で訂正）

`tools:` は**許可リスト**であり、`Agent`（サブエージェント起動ツール。旧称 Task）を
明記していない agent は**構造的に委譲できない**。

- **委譲できるのは `jen-pmo` だけ**（`tools:` に `Agent` を持つ唯一の agent）。
  オーケストレーションの単一責任をここに集約している。
- worker（builder / architect / debugger 等）は `Agent` を持たない。
  探索が必要でも自分でscoutを起動することはできず、**PMOへ差し戻す**。
- v3.7以前は「builder/architect/debugger が自分専用の scout を起動してよい」と
  記載していたが、どの agent も `tools:` に `Agent` を持っておらず**実現不能な
  記述だった**ため撤回した。

> ⚠️ 未検証: インタラクティブセッション（fork mode ON が既定）ではサブエージェントは
> background 実行になり、公式ドキュメントの「background subagent が保持する組み込み
> ツール」一覧に `Agent` は含まれていない。一方で「既定で3階層まで入れ子にできる」
> という記述もあり競合している。jen-pmo が委譲できない場合の回避策は
> `references/relay-protocol.md`「前提条件」を参照。
