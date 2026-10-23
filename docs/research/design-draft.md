# 設計草案（0周目時点・Anthropic/Sakana の一次情報待ち）

出典は全て `sources/` の原文の行番号。**これは私の導出であって原文の要約ではない。**

## P1 停止は「証拠の被覆」で決める。確信度では決めない
HALT L25-27「stopping as evidence coverage rather than generator confidence」
- 受入条件を事前に K 個の atomic claim に分解する
- claim ごとに **単調非減少**の状態 NULL→PARTIAL→MATCH（running max・HALT L213-217）
- 全 claim が MATCH で初めて停止（ALL_MATCH・HALT L235-237）
- → **合成は決定論、判定だけがモデル**

## P2 判定は極小に割る。巨大な問いを1回聞かない
HALT L182「A verifier Vθ assigns each claim–sentence pair」
- Jen の現状: verifier に「ACCEPT/REJECT」を聞く＝巨大な1問。外れると全部外れる
- HALT: claim×evidence の対ごとに3値＝極小の多数問。安い模型で安定し、
  かつ「**どの主張が埋まっていないか**」が機械的に分かる
- Vθ は分類ヘッドを足さず、3つのラベル文字列の長さ正規化log確率の argmax（L231-236）
  → LLM judge でも同じ形に落とせる（保証は下がる）

## P3 分岐は選択的に。常時分岐は負ける
HypoSearch アブレーション L774-790「Always Branch ... substantially increases tool calls and latency.
In contrast, HYPOSEARCH achieves the best accuracy while using fewer tool calls and lower latency」
- divergent state を**検出してから**分岐する
- 検出の判断基準（L824-842 のプロンプトより）: 「Difficult does not mean divergent」
  「A single obvious evidence gap is direct」「When uncertain, choose direct」
- 分岐ごとに**局所予算**＋早期終了3条件（十分な証拠／矛盾に当たった／上限）L776-784

## P4 コミット前に比べる。コミット後の是正は効かない
HypoSearch L23-34「subsequent tool calls tend to reinforce the same path」
- Jen の現状: 同一手法2回目で STUCK＝**事後**。すでに道に乗ってから気づく
- 要るのは分岐点でコミット前に分けること

## P5 失敗は2方向ある。片方だけ塞ぐと逆に倒れる
Zhang L35-40「over-search ... and under-search」／HALT L339-343
- 3B は予算まで走る（78–88%・過剰）、7B は被覆前に止まる（51/64/79%・過少）
  → **規模で向きが逆転する**
- Jen の空転検知・ブレーカーは over 側のみ。**under 側（早すぎる完了）のガードが無い**
- P1 の ALL_MATCH は under 側のガードとして効く（被覆が埋まるまで止まれない）

## P6 早すぎる要約は探索を妨げる
Kuhlthau 1991（`kuhlthau-1991-inside-search-process.txt`）
- v3.8 の伝言役・原文保全（`.jen/inbox.md`）は**この研究と同じ結論**。体感で当てていた
- 維持する。むしろ強化する

## P7 問いは途中で変わる。固定しない
Bates 1989（`bates-1989-berrypicking.txt`）
- Jen の `mission.md` は固定扱い。変更を許し理由をログに残す形にすべき
- ただし P1 と衝突する: claim を変えれば被覆もリセットされる
  → **claim の改訂は版を切って記録し、被覆を引き継がない**設計にする

## P8 飽和は「診断」として使う。**停止則としては使わない**（原文確認で判断変更）
Kastner ら 2007（`sources/kastner-2007-horizon-estimate.txt`・ユーザー供給で入手）
- 推定器は機能する: 4DBで既知1246件に対し Horizon 1838件 95%CI[1749,1955]、捕捉率68%（L197-198, L35-37）
- 前向きの停止則の形: 「stop if the known number of articles falls within the confidence
  intervals of the horizon estimate」（L234-237）
- **だが採用しない理由（すべて原文）**:
  - L222-228「how close we need to get to the Horizon to be credible」を決める定義は**未確立**と明言
  - L231 検証は**後ろ向きのみ**
  - L240-243 **著者自身のデータで停止条件は一度も発火していない**（1246 は CI[1749,1955] に入らない）
- → 採るのは「今どれだけ取りこぼしているかの推定値を**出す**」ところまで。
  「だから止めてよい」の判断には使わない。**停止は P1（証拠の被覆）が担う**

## 未決（Anthropic/Sakana の報告待ち）
- C2 Anthropic の一次情報が、上の P1-P8 と衝突するか補強するか
- C3 Sakana の自己改善・進化的手法が、P3（選択的分岐）と同じ構造か別物か
- 「考えうる最高」を名乗る前に、この2つを外したままにはしない
