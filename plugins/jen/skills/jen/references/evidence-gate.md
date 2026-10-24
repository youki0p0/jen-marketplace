# 証拠ゲート（v4）— 完了を「証拠がそろったか」で決める

v3 までの Jen は、**ほぼ全部がプロンプト**だった。「ガード」と呼んでいたものは
(a) Bash への正規表現9本（`pre_tool_guard.py`・32行）か、
(b) **LLM に従うようお願いしている文**のどちらかで、機械的に動く仕組みは合計67行しかなかった。
`post_tool_log.py` は全ツール呼び出しを生 JSONL に流すだけで、受入条件との紐付けは無い。

v4 で、**完了の判定だけ**をプログラムに移す。

## 核になる考え

> **1件ずつの判断はモデルに聞き、全部そろったかの集計はプログラムがやる。**

v3 の verifier は「受入条件を満たしたか？」という**巨大な問いを1回**聞いていた。
外れると全部外れる。v4 は「**この1つの証拠は、この1つの項目を裏づけるか**」という
小さい質問に割り、**全項目がそろったかの集計を Python でやる**。

出典: HALT (Roh & Han 2026, arXiv 2608.02009)。
「We frame stopping as evidence coverage rather than generator confidence」。
HALT 自身は Qwen2.5-3B + LoRA の検証器を使うが、Jen は AXIOM-0（Claude のみで完結）
により他社モデルを使わない。極小の判定は haiku サブエージェントが担い、
running max と ALL_MATCH の合成は `evidence_ledger.py` が担う。

## 証拠の3段階（ここが v4 の肝）

コキエ 2026-03 の実験で、**文字列ベースの proof は破られている**。Stop Hook が出力中の
`<proof>QUALITY_GATE_PASSED</proof>` を見ていたため、モデルはその文字列を出力するだけで
通した。本人の分析は「心理ではなく訓練分布の問題」——指示に含まれる文字列をそのまま
出力するのは頻出パターンだから。

| 強度 | 証拠の形 | 誰が作れるか | 偽造 |
|---|---|---|---|
| `weak` | `attest --kind note`（エージェントの申告） | エージェント | **自由** |
| `medium` | `attest --kind artifact`（ファイル。台帳が sha256 を計算） | エージェント | 意図が要る |
| **`strong`** | **`run --cmd`（台帳が自分で実行し終了コードを捕まえる）** | **台帳だけ** | **トークン出力では不能** |

**強い証拠を宣言する CLI 経路は用意していない。** `run` しか作れない。
`require` の既定は `medium` で、大事な項目は `strong` にする。

道具（MCP・外部コマンド）が使えるなら `run` の中身を強くできる。
ブラウザ自動化の実行結果、実 HTTP 応答、テストの終了コードは、
エージェントが**トークンでは作れない**。Anthropic も Puppeteer での検収を
「dramatically improved performance」と書いている
（effective-harnesses-for-long-running-agents）。

## 検証を、いつ走らせるか — ここが設計の中心

**独立した検収は常に必要。変わるのは走らせる頻度だけ。**
これは2つの独立した一次情報が同じ結論に達している。

- Jain 2026-10（martinfowler.com）: 同一課題をハーネス有無で比較。
  フロンティア（GPT-6 Sol）は**どちらでも 10/10**、ハーネスは時間とコストだけ増やした。
  低コスト（GPT-6 Luna）は素 **3/10 → ハーネス付き 10/10**。
  代償は平均 **+1,707万トークン・+19分・$0.187/試行**（素のベースラインの約16倍）。
  結論「What changes with model capability is not whether independent sensors are
  needed, but **when they run**」。Sonnet 4.6 / Opus 4.6 も素で初回成功している。
- Anthropic 2026-03（harness-design-long-running-apps）: 自作ハーネスが
  「bulky, slow, and expensive」だったので **sprint construct を丸ごと削除**し、
  **evaluator を毎スプリントから最終1回に移した**。理由は Opus 4.6 の改善。
  「the evaluator is **not a fixed yes-or-no decision**. It is worth the cost when
  the task sits beyond what the current model does reliably solo」。
  planner は残した（無いと generator が under-scope するため）。

Jen の実装:

| tier | sensor_mode | 意味 |
|---|---|---|
| `haiku` / `sonnet` | `continuous` | 工程ごとに `run` で証拠を足していく。**安いモデルではハーネスの効果が実験で出ている** |
| `opus` | `final_gate` | 工程中は回さず、Stop ゲートで1回だけ検める |
| `fable` | `final_gate` | opus と同扱い。**優先度低**（2026-10 時点の実測性能が良くないため未検証） |

Jen は18体中12体が `sonnet` なので、投資先と実稼働が一致する。
`evidence_ledger.py tier --set opus` で切り替わる。

> ⚠️ v3.8.3 の注記: **Opus 5.5 は effort の既定が `medium`**（Opus 5 は `high`）。
> 同じ `model: opus` でも実効的な思考量が変わるので、`final_gate` が妥当かは
> effort も見て判断する。effort を下げた opus は `continuous` 寄りに戻す余地がある。

## 受入条件が変わったら証拠は引き継がない

Bates 1989（berrypicking）が示すとおり、調べ・作業の途中で問いは変わる。
`mission.md` を固定扱いにすると、変わった受入条件に古い証拠が付いたままになる。

`evidence_ledger.py revise --note '<理由>'` が版（`mission_rev`）を切り、
**全項目の状態と証拠を消す**。引き継がないのが正しい
（古い項目に付いた証拠は、新しい項目を裏づけない）。

## 偽造耐性の正直な限界

**暗号的に防げてはいない。** 封印（seal）は台帳自身が既知の方法で計算するので、
スクリプトを読めるエージェントは偽造後に再計算できる。防げているのは3層:

1. 不注意な書き換え（リダイレクト・`sed -i`）→ 封印の不一致で検出
2. よくある編集経路 → PreToolUse（`guard_patterns.LEDGER_PATTERNS`）で拒否
3. ログの実体が無い `strong` → `orphan_strong()` で検出（封印を再計算されても捕まる）

つまり「**カジュアルな抜け道を塞ぎ、事後に検出可能にする**」まで。
決意したエージェントは止められない。コキエの結論と同じで、安全性ではなく訓練分布の話。

**最も強い層は封印ではなく `run` の存在そのもの。** 台帳が自分で実行する限り、
エージェントは「テストが通った」を出力で作れない。

## 台帳が無いセッションの扱い（妥協を明示する）

プラグインは全セッションで有効になるので、台帳が無いだけで停止を塞ぐと
普通の会話すら終われない。したがって**台帳の存在がゲートの opt-in**。

「台帳を作らなければ回避できる」穴は残る。塞ぐ代わりに、
**ゲート無しで終わったことを必ず記録する**（`.jen/logs/stop-events.jsonl` の
`gated: false`）。行動監査（`/jen:jen-audit`）が拾えるので事後に数えられる。
**穴を黙って残すのではなく、見えるようにしてから残している。**

人間が明示的に切る経路も用意する（`.jen/claims.json` の `"gate": "off"`）。
切ったことは `reason: gate_off_by_human` として記録される。

## 各部品が前提している「モデルの不足」（P9）

> **ハーネスの各要素は、モデルができないことの仮定である。**
> （Anthropic / harness-design-long-running-apps）

部品は、**モデルにこれができない**という仮定の上に立っている。
モデルが良くなればその仮定は外れ、部品は効果のない費用だけになる。
これが日本語圏の「自作オーケストレータを解体した」報告5件
（yamk / Gota「やりすぎた話〜そのハーネスは解体された」/ 奥山「モデルの進化との
付き合い方」/ tororo / shimo4228）と、Jain のフロンティア結果を同時に説明する。
**前提にしていたモデルの弱点が解消された、と見るほうが合う。**

| 部品 | 前提している不足 | 外し方 |
|---|---|---|
| `evidence_ledger.py` の判定 | モデルは自分が終わったかどうかを甘く見積もる | `require` を下げる → 台帳を使わない |
| 証拠強度3段階 | モデルは弱い証拠を強い証拠と見なす | 既定 `require` を `weak` へ |
| `stop_gate.py` | モデルは早すぎる完了宣言をする | `sensor_mode: final_gate` → hooks から外す |
| モデル別の検証頻度 | 安いモデルは継続的に見ていないと外れる | tier 表を書き換える（この表自体が、仮定を管理する場所） |
| `LEDGER_PATTERNS` | モデルはゲートを通すため証拠を偽造する | 外す（ただしコキエの実験は 2026-03 時点で再現している） |
| `PATTERNS`（破壊的操作） | — | **外さない。** 人間の承認が要るのは能力ではなく権限の問題 |

最後の行だけ期限がない。他は全部、いつか外す前提で書いてある。

## 検討して不採用にしたもの

### Horizon 推定（capture-mark-recapture）を停止則にする案 — **不採用**

一次情報: Kastner M, Straus S, Goldsmith CH. *Estimating the Horizon of Articles to
Decide When to Stop Searching in Systematic Reviews.* AMIA Annu Symp Proc. 2007:389-393.
PMCID: PMC2655834 / PMID: 18693864（本文は PMC で無料。本リポジトリには置かない）

生態学の capture-mark-recapture を文献検索へ応用し、複数ソースの重複から
未発見件数を Poisson 回帰で推定して全体数（Horizon）を 95% 信頼区間つきで出す手法。
「既知件数が Horizon の信頼区間に入ったら停止」という停止則が導ける。
Jen の飽和判定（「2サイクル台帳無変化でブレーカー」）より定量的に見えたので検討した。

**原文を読んで不採用にした。要約だけでは出ない3点が書いてある:**

1. 「how close we need to get to the Horizon to be credible」を決める定義は
   **未確立**と著者自身が明言している（More studies are needed ... to derive and
   validate a definition）。つまり**停止の閾値が無い**。
2. 検証は**後ろ向きのみ**。前向きに回した結果は無い。
3. 決定的なのはこれ: **著者自身のデータで、その停止条件は一度も発火していない**
   （既知1246件に対し Horizon 推定の95%CIは[1749,1955]で、
   どの段階でも既知件数がCIに入らなかった）。

推定器そのものは機能する（4DBで捕捉率68%・取りこぼし592件と算出できている）。
したがって**「今どれだけ取りこぼしているかの推定値を出す」診断としては使える**が、
**「だから止めてよい」の判断には使わない**。停止は証拠がそろったか（上記 ALL_MATCH）で決める。

この判断を記録に残す理由: 要約だけ読むと「前向きに使えば停止ルールになる」と読めるため、
一次情報を読まずに再検討すると同じ結論に戻れない。**未検証の停止則をハーネスの
中核に入れる事故**を防ぐための記録である。

## 測れていないこと（最重要の留保）

**「hook で強制した検証ループ vs プロンプトのみ」の完了率を比較した研究は、
2026-10 時点の調査では見つからなかった。** Jain は「ハーネス有無」を比較しているが、
強制手段が hook かプロンプトかは比較していない。Anthropic は feature list の保全を
「strongly-worded instructions（`It is unacceptable to remove or edit tests because...`）」
——つまり**プロンプト**で守っている。コキエの実験は、それが偽造可能だと示している。

したがって v4 は**未測定領域にある**。効果を断言しない。
`.jen/logs/stop-events.jsonl` の `gated` / `passed` が溜まるので、
同種タスクで `gate: off` と既定を切り替えて比べれば、**自分で測れる**。
測ったら `.jen/decisions.md` に残すこと。

## 使い方

```bash
H="${CLAUDE_PLUGIN_ROOT}/hooks"

# 受入条件を、1つずつ確かめられる項目に割って台帳を作る（PMO の仕事）
python3 "$H/evidence_ledger.py" init --tier sonnet \
  --claim "C1=lint / typecheck / test が通る" \
  --claim "C2=初回画面に次アクションが表示される"

# 大事な項目は強い証拠を要求する
python3 "$H/evidence_ledger.py" claim-add --id C3 \
  --text "既存テストを壊していない" --require strong

# 台帳が自分で実行して、終了コードを強い証拠にする
python3 "$H/evidence_ledger.py" run --claim C1 --cmd "npm test"

# どの項目に証拠がそろったか（全 MATCH で exit 0）
python3 "$H/evidence_ledger.py" status

# 受入条件が変わったら版を切り替える（証拠は消える）
python3 "$H/evidence_ledger.py" revise --note "受入条件に対応端末を追加した"
```

試験: `python3 -m unittest discover -s tests -v`（16件・標準ライブラリのみ）
