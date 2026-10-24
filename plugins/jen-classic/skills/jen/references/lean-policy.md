# jen-classic の方針 — 少ないコンテキストとトークンで、同じ結果を出す

**これは jen-classic の存在理由である。** v3 までの jen-classic は「Fable不要版」、つまり
欠けているものを**補償する**版として定義されていた。v4 で再定義する:

> **jen-classic は、同じ仕事をより少ないトークンと時間で終わらせるための版である。**
> Fable を使わないのは制約ではなく、結果としてそうなるだけ。

Fable版（`jen`）は「指揮に高単価モデルを置き、長時間の一貫性を買う」。
`jen-classic` は「**同じ仕事を、より少ないトークンと時間で終わらせる**」。
目的が違うので、既定値が違う。

## 支配的な判断則（これだけ覚えればよい）

Tran & Kiela 2026（Stanford, arXiv 2604.02460）が、情報理論（Data Processing
Inequality）に基づいてこう述べている:

> 「under a fixed reasoning-token budget and with perfect context utilization,
> **single-agent systems are more information-efficient**」（要旨 L25-29）
>
> 「this perspective further predicts that **multi-agent systems become competitive
> when a single agent's effective context utilization is degraded, or when more
> compute is expended**」（要旨 L29-31）

したがって `jen-classic` の委譲判断は1行に落ちる:

> ### 委譲するのは、単一エージェントの**実効的なコンテキスト利用が劣化する**ときだけ。
> それ以外は単一で回す方が情報効率が高い。「18体いるから振る」は理由にならない。

同論文は、報告されている多エージェントの優位の多くが
「**unaccounted computation and context effects**」で説明され、
アーキテクチャ固有の利点ではないとも述べている（要旨 L39-44）。
計算量を揃えると差は消える。`jen-classic` はこれを前提に設計する。

## 既定値（Fable版との差）

| | jen（Fable版） | **jen-classic** | 根拠 |
|---|---|---|---|
| 既定の動き | 分解して委譲 | **単一で回す。** 委譲はコンテキスト劣化時のみ | 2604.02460 L25-31 |
| 開始モデル | sonnet | **haiku から試す。**昇格は verifier REJECT 後 | 実測の失敗だけを昇格の根拠にする |
| 並列ファンアウト | 独立タスクは並列 | **既定で行わない** | Cursor: 20体でロックの実効スループットが2〜3体分に低下／CooperBench: 協働で成功率が平均30%低下 |
| 最終昇格 | deep-solver 単独 | **opus合議は opt-in**（既定は単発昇格） | 合議は構造上3倍の計算を使う＝効率機構ではない |
| コンテキストスコープ | 必須 | **必須。かつ先に codemap を引く** | v3.6（Graft 系）。`jen-classic` では省略不可 |
| 検証の頻度 | opus なので最後に1回 | **連続**（安い層で回すため） | Jain 2026: 低価格モデルはハーネスなしで 3/10、付きで 10/10 |
| 数える単位 | — | **仕事1件を終えるまでに使った量**（1回の呼び出しあたりではない） | 安いリクエストが往復を増やすなら安くない |

## 合議制を opt-in に落とした理由

v3 の jen-classic の看板は「opus合議制（architect + debugger の独立仮説 → deep-solver が統合）」
だった。これは**悪い機構ではない** — 独立仮説の突き合わせで単独モデルの思い込みを相殺する、
という狙いには筋がある。

しかし **`jen-classic` の既定にはできない。** 合議は定義上 opus を3回以上呼ぶ。
2604.02460 の言う「more compute is expended」に真っ向から該当するので、
「同じ仕事を、より少ないトークンと時間で」という目的と衝突する。

したがって:
- **既定は単発昇格**（opus 1回）。
- 合議は**人間が明示的に要求したときだけ**（「合議で」「council」と言われたとき）。
- 合議を使ったら `.jen/decisions.md` に「なぜ3倍払う判断をしたか」を1行残す。

機構は消していない。既定から外しただけである。

## 使った量を数える（`evidence_ledger.py budget`）

「少ないトークンで」を標語で終わらせない。**数える。**

`jen-classic` でいちばん費用がかさむのは**ほかのエージェントに任せた回数**である。サブエージェントは呼び出しごとに
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

## agent を証拠能力で分類する（削らない理由）

「自分で片づけるのが既定」になると、18体の agent の出番がなくなるように見える。
だが**削らない。** 費用が増えるのは「**理由を言えないまま任せたとき**」である。
一覧に何体並んでいるかは費用と無関係である。
削除は不可逆で capability を失う一方、得られるのは「一覧が短くなる」だけ。

代わりに、v4 の証拠ゲートが自動的に引いてくれる線で分類する。
完了は証拠がそろったかで決まるので、各 agent は**どの強さの証拠を作れるか**で分かれる:

| 作れる証拠 | agent | 扱い |
|---|---|---|
| **strong**（台帳が実行して終了コードを取れる成果） | builder / frontend / test / debugger / verifier / strict-verifier | **既定経路** |
| **medium**（file:line の引用を返す） | scout / release-manager | **既定経路**（scout は省略不可） |
| medium（外部の一次情報を引く） | research | opt-in |
| **weak のみ**（意見・分析） | ux-critic / contrarian-reviewer / monetization-reviewer / product-strategist / ideation | **opt-in** |

**最後の群が既定から外れる理由は、好みではなく構造である。**
意見は `attest --kind note` = `weak` にしかならず、既定の `require=medium` に届かない。
つまり**呼んでも項目は MATCH にならず、完了には近づかない**。
価値が無いのではなく、**完了判定とは別の軸**にある。

例外: **jen-security-reviewer は条件付きで必須**。auth / payment / secret /
security 境界に触るときは省略しない。これは Human Gate のトリガと同じ条件であり、
「証拠を作れるか」ではなく「踏んだら戻れないか」で判断する軸だから
（Claude のみで完結する方針と同じく、期限のない決まり）。

opt-in の群を呼ぶときは、`board.md` に**何を決めるために呼んだか**を書く。
書けないなら呼ぶ理由が無い。

この扱いは opus合議制を既定から外したのと同じである——**機構は残し、既定から外す**。

## やらないこと（`jen-classic` で意図的に省くもの）

- **「念のため」の委譲。** reviewer を全部通す、のような網羅は `jen-classic` ではしない。
  必要だと**判断した根拠**を言えないレビューは呼ばない。
- **予防的な昇格。** 「難しそうだから opus」はしない。REJECT が出てから上げる。
- **並列化の既定化。** 並列は速いが安くない。壁時計時間が本当に制約のときだけ。
- **全体を読ませる指示。** 「リポジトリ全体を読んで」は `jen-classic` では禁止。
  scout に codemap を引かせ、対象ファイルだけ渡す。

## Fable版と同時に有効化しないこと

agent 名が共通なので競合する。**どちらか片方**だけを入れる。
選び方:

- **難しい仕事を解けるようにしたい** → `jen`（Fable版）。長時間の一貫性にトークンを使う。
- **同じ仕事を少ないトークンで終わらせたい** → `jen-classic`。

なお AXIOM-0（Claude のみで完結）は両版で同じく最上位の制約である
（`references/axiom-0.md`）。`jen-classic` は「安いから外部サービスを使う」をしない。
