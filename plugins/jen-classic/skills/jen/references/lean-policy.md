# Lean 方針 — 最小のコンテキスト・トークン・資源で最大の成果

**これは jen-classic の存在理由である。** v3 までの jen-classic は「Fable不要版」、つまり
欠けているものを**補償する**版として定義されていた。v4 で再定義する:

> **jen-classic は、同じ成果をより少ない資源で出すための版である。**
> Fable を使わないのは制約ではなく、結果としてそうなるだけ。

Fable版（`jen`）は「指揮に高単価モデルを置き、長時間の一貫性を買う」。
Lean版（`jen-classic`）は「**払わないことで勝つ**」。目的が違うので、既定値が違う。

## 支配的な判断則（これだけ覚えればよい）

Tran & Kiela 2026（Stanford, arXiv 2604.02460）が、情報理論（Data Processing
Inequality）に基づいてこう述べている:

> 「under a fixed reasoning-token budget and with perfect context utilization,
> **single-agent systems are more information-efficient**」（要旨 L25-29）
>
> 「this perspective further predicts that **multi-agent systems become competitive
> when a single agent's effective context utilization is degraded, or when more
> compute is expended**」（要旨 L29-31）

したがって Lean 版の委譲判断は1行に落ちる:

> ### 委譲するのは、単一エージェントの**実効的なコンテキスト利用が劣化する**ときだけ。
> それ以外は単一で回す方が情報効率が高い。「18体いるから振る」は理由にならない。

同論文は、報告されている多エージェントの優位の多くが
「**unaccounted computation and context effects**」で説明され、
アーキテクチャ固有の利点ではないとも述べている（要旨 L39-44）。
計算量を揃えると差は消える。Lean 版はこれを前提に設計する。

## 既定値（Fable版との差）

| | jen（Fable版） | **jen-classic（Lean版）** | 根拠 |
|---|---|---|---|
| 既定の動き | 分解して委譲 | **単一で回す。** 委譲はコンテキスト劣化時のみ | 2604.02460 L25-31 |
| 開始モデル | sonnet | **haiku から試す。**昇格は verifier REJECT 後 | 実測の失敗だけを昇格の根拠にする |
| 並列ファンアウト | 独立タスクは並列 | **既定で行わない** | Cursor: 20体でロックの実効スループットが2〜3体分に低下／CooperBench: 協働で成功率が平均30%低下 |
| 最終昇格 | deep-solver 単独 | **opus合議は opt-in**（既定は単発昇格） | 合議は構造上3倍の計算を使う＝効率機構ではない |
| コンテキストスコープ | 必須 | **必須。かつ先に codemap を引く** | v3.6（Graft 系）。Lean 版では省略不可 |
| センサー頻度 | opus で最終ゲート1回 | **連続**（安い層で回すため） | Jain 2026: 低コストモデルで素 3/10 → ハーネス付き 10/10 |
| 計測の単位 | — | **完了タスクあたりの資源**（リクエストあたりではない） | 安いリクエストが往復を増やすなら安くない |

## 合議制を opt-in に落とした理由

v3 の jen-classic の看板は「opus合議制（architect + debugger の独立仮説 → deep-solver が統合）」
だった。これは**悪い機構ではない** — 独立仮説の突き合わせで単独モデルの思い込みを相殺する、
という狙いには筋がある。

しかし **Lean 版の看板にはできない。** 合議は定義上 opus を3回以上呼ぶ。
2604.02460 の言う「more compute is expended」に真っ向から該当するので、
「同じ成果をより少ない資源で」という目的と衝突する。

したがって:
- **既定は単発昇格**（opus 1回）。
- 合議は**人間が明示的に要求したときだけ**（「合議で」「council」と言われたとき）。
- 合議を使ったら `.jen/decisions.md` に「なぜ3倍払う判断をしたか」を1行残す。

機構は消していない。既定から外しただけである。

## 資源を測る（`evidence_ledger.py budget`）

「最小の資源で」を標語にしない。**数える。**

Lean 版の支配的なコストは**委譲回数**である。サブエージェントは呼び出しごとに
まっさらなコンテキストで始まるので、1回の委譲は1つのコンテキストウィンドウを丸ごと使う。
トークン数そのものは Jen の内側からは見えないが、**委譲回数は hook の実ログから数えられる**
（`post_tool_log.py` が `.jen/logs/tool-events.jsonl` に全ツール呼び出しを記録している）。

```bash
# ミッション開始時に上限を宣言する
python3 "$H/evidence_ledger.py" init --tier haiku --max-delegations 8 --claim "C1=..."

# 現在の消費を見る（実ログから数える。自己申告ではない）
python3 "$H/evidence_ledger.py" budget
```

超過しても**強制停止はしない**（v3.4 以来の不変条件どおり、数値による hard-stop はしない）。
超過は「この分解は重すぎたのではないか」という自己点検シグナルとして扱い、
`.jen/decisions.md` に残す。

> ⚠️ 正直な限界: PostToolUse のペイロードに委譲先が含まれるかはハーネスの実装依存で、
> Jen 側では検証していない。数えられなければ `budget` は「判定不能（ログ不足）」を返す。
> 黙って 0 とは言わない。

## やらないこと（Lean 版で意図的に省くもの）

- **「念のため」の委譲。** reviewer を全部通す、のような網羅は Lean 版ではしない。
  必要だと**判断した根拠**を言えないレビューは呼ばない。
- **予防的な昇格。** 「難しそうだから opus」はしない。REJECT が出てから上げる。
- **並列化の既定化。** 並列は速いが安くない。壁時計時間が本当に制約のときだけ。
- **全体を読ませる指示。** 「リポジトリ全体を読んで」は Lean 版では禁止。
  scout に codemap を引かせ、対象ファイルだけ渡す。

## Fable版と同時に有効化しないこと

agent 名が共通なので競合する。**どちらか片方**だけを入れる。
選び方:

- **成果の天井を上げたい** → `jen`（Fable版）。長時間の一貫性に金を払う。
- **同じ成果をより安く出したい** → `jen-classic`（Lean版）。

なお AXIOM-0（Claude のみで完結）は両版で同じく最上位の制約である
（`references/axiom-0.md`）。Lean 版は「安いから外部サービスを使う」をしない。
