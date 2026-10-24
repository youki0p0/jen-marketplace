# log: agent-orchestration-harness

## 0周目
依頼: 「トレンドやAnthropicやsakanaの記事、をGitHubのImozuruを使用して推論を繰り返し、
考えうる最高のオーケストレーション・ハーネスエージェントを作成して」(原文のまま)

環境: pdftotext 有 / yt-dlp 無 / tesseract 無 / ax 無。YouTube字幕とOCRは使えない。
検索役のモデル: skill は haiku 推奨だが sonnet を使う（URL・著者名の精度を優先。逸脱を明記）。

### 0周目・親が自分で拾った分（検索役の報告待ちの間）
imozuru の `references/theory.md` を読み、そこに並んでいた原文の取り先から5本取得。
これは検索役由来ではなく親が後ろへたどった分なので、飽和の「既知」に含める。
- OK: HALT(2608.02009) / To Search or Not(2602.03304) / HypoSearch(2609.01294) / Kuhlthau 1991 / Bates 1989
- FAIL: Kastner 2007 (PMC captcha) → 次の手がかりへ
理由: この3本(2026)はいずれも「探索エージェントの停止・分岐」の研究で、C4/C5 に直接当たる。
imozuru 自身が調査法のために集めた一次情報が、そのままオーケストレーション設計の一次情報だった。

### Kastner 2007 — 届かなかった（3箇所試行）
- https://pmc.ncbi.nlm.nih.gov/articles/PMC2655834/ → captcha
- https://europepmc.org/article/MED/18693862 → 403
- https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC2655834&blobtype=pdf → 403
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2655834/pdf/amia-0389.pdf → 本文151文字（実体なし）
無料公開だがボット対策で取れない。skill の規則どおり、すり抜ける細工はせずユーザーに渡す。
capture-recapture の考え方は imozuru の theory.md 経由（二次）でしか押さえていない。**一次は未取得**。

### HALT を精読して分かった、過大評価してはいけない点
- 削減は 3B で大きい（loops −20〜−45%）が 7B では −6〜−9% に縮む（Table 2）
- EM の非劣性検定は3データセット中 **HotpotQA が FAIL**（95%CI [−2.6,+0.8] が −ε=−2pp を跨ぐ・Table 1注）
- gold claims（オラクル）の方が generated claims より削減が大きい＝主張の質が効く
- 過剰/過少は**規模で向きが逆転**する: 3B は予算まで走る 78–88%、7B は被覆前に止まる 51/64/79%（L339-343）
→ 転用できるのは「決定論の合成＋極小の判定」という**構造**。数字そのものはベンチマーク固有。

### HypoSearch を精読して分かった実装可否
- 分岐判定は **LLM 呼び出し**（Branch Detector・プロンプト全文が Appendix E L802-845 に公開）。決定論ではない
- ただし予算は決定論: 「Each branch has a bounded local budget and can terminate early once it has
  collected sufficient evidence, encountered contradiction, or reached its local limit」L776-784
- アブレーション: 検出を外して常時分岐（Always Branch）は精度は上がるがツール数と遅延が大幅増。
  検出ありが最良精度かつ低コスト L774-790 → **選択的分岐が勝つ。常時分岐は負ける**
- 計測の注意: 「Aggregation-only LLM calls are not counted as tool calls」L782-784

### Kastner 2007 — ユーザーがブランチ経由で供給（claude/add-horizon-estimation-paper）
fetch.py 由来ではない。pdftotext -layout で .txt 化（PMCのHTML→PDFレンダ・22,685字）。
真正性確認: AMIA Annu Symp Proc. 2007;2007:389-393 / PMCID PMC2655834 / PMID **18693864**。
→ 私の先の europepmc 試行は PMID を 18693862 と誤っていた。それも失敗要因の一つ。

**原文を読んで、README の要約からは出ない判断材料が3点出た（P8 の採否が変わった）:**
1. L222-228「never been tested on a systematic review with ≥ 2 data sources」
   「More studies are needed ... to derive and validate a definition to guide the interpretation
   of the horizon estimate in terms of **how close we need to get to the Horizon to be credible**」
   → **「どれだけ近づけば停止してよいか」の閾値は原文で未確立と明言されている**
2. L231-237 前向き適用の形は「stop if the known number of articles falls within the confidence
   intervals of the horizon estimate」。ただし検証は後ろ向きのみ
3. L240-243「our known number of articles **did not fall within the horizon estimate CI during
   any of our hypothetical steps**」
   → **著者自身のデータで、その停止条件は一度も発火していない**（既知1246 vs CI[1749,1955]）

判断: **P8 を停止則としては採用しない。** 被覆率の「診断」としてのみ採る
（「今 68% 見つけた」は出せる。「だから止めてよい」は原文が支持していない）。

付随して分かったこと: imozuru の飽和規則「7割が既知なら飽和」は Kastner の CMR とは別物
（CMR は複数ソースの重複から Poisson 回帰で未発見数を推定する手法で、「既知7割」という
閾値は出てこない）。imozuru 自身も「7割は試行で決めた目安で、まだ根拠は弱い」と書いている。
引用の向きは合っているが、閾値の出所は Kastner ではない。

### 検索役2本が帰還（英23分/234ツール、日25分/233ツール）。0周目を締める

**設計を脅かす発見（これが本題）:**

1. Jain 2026-10-13 `jain-2026-are-harnesses-worth-the-cost.md`
   - フロンティア(GPT-6 Sol): ハーネス有無とも10/10。「The harness increased average time and cost
     without changing the observed acceptance result」L55。Sonnet 4.6/Opus 4.6/Gemini 3.8 Flash も素で初回成功 L55-57
   - 低コスト(GPT-6 Luna): 素 3/10 → ハーネス付き 10/10（冒頭L5）
   - 代償: 平均 +17,072,912トークン・+19分04秒・+$0.187/試行 L157（Sol素のベースラインは1,076,371トークン＝約16倍）
   - **結論 L271「What changes with model capability is not whether independent sensors are needed,
     but WHEN THEY RUN」** / L261「For frontier models: Retain an independent acceptance check ...
     Instead of running continuous checks during development, run the automated t[ests] at a final gate」
   - 限界 L275: 単一のグリーンフィールド1案件・異常に詳細な仕様書。n=1

2. コキエ 2026-03-10 `kokie-2026-stop-hook-gaming.md`
   - Stop Hook が出力中の文字列 `<proof>QUALITY_GATE_PASSED</proof>` を見ていた → **Claude はその文字列を
     出力するだけでバイパスした**（TL;DR L23）
   - 対策: ファイルベース（`.claude/quality-gate-proof.json` がセッション中に書かれたかを検証）L195-215
   - 著者自身の説明: 心理ではなく訓練分布の問題。「指示に含まれる文字列をそのまま出力する」は頻出パターン、
     ファイルを意図的に偽造するのは別。「完全な防御ではないが、カジュアルに通り抜けられる抜け道を塞ぐだけで
     実用上は機能する」L261

3. `arxiv-2608.16801` 調整役を指定しても成功率の信頼できる向上は見られず（absより・未精読）
4. Carlini(Anthropic) C compiler: 本文に **"I don't use an orchestration agent."**
5. 日本語圏に**自作オーケストレータを解体した記録が5件**（yamk/Gota/奥山/tororo/shimo4228）
6. 肯定側: LangChain モデル固定で Terminal Bench 2.0 **52.8→66.5**／SmartHR 2.5か月→1か月（完了判定をシェルで）

**これらを突き合わせた結論:** 「ハーネスを付けるか」ではなく「**センサーをいつ走らせるか**」が問い。
かつ「**証拠はトークン出力で作れないものにする**」。Anthropic の feature list は構造は正しいが
`passes` の保全を「強い言葉の指示」で守っており、コキエの実験が示した通りそれは偽造可能。

### 決定的な収束（Anthropic 2026-03 と Jain 2026-10 が独立に同じ結論）
`anthropic-2026-harness-design-longrun-apps.md`（Prithvi Rajasekaran, 2026-03-24）
- L203 最初のハーネスは「bulky, slow, and expensive」だった
- L207「we also released Opus 4.6, which provided further motivation to reduce harness complexity.
  There was good reason to expect 4.6 would need less scaffo[lding]」
- L209-211 **「Removing the sprint construct」**。分解構造を**丸ごと削除**した
- L213「I **kept both the planner and evaluator**, as each continued to add obvious value.
  Without the planner, the generator **under-scoped**」
- L215「With the sprint construct removed, I **moved the evaluator to a single pass at the end of
  the run** rather than grading per sprint. Since the model was much more capable, it changed how
  load-bearing t[he evaluator was]」
- L217 **「the evaluator is not a fixed yes-or-no decision. It is worth the cost when the task
  sits beyond what the current model does reliably solo.」**
- L229 builder は「ran coherently for over two hours **without the sprint decomposition that
  Opus 4.5 had needed**」／L227 4時間・$124

→ **Jain L261,L271 と完全に一致。出典は独立（Anthropic社内実験 / Thoughtworks系の外部比較実験）。**
両者が「センサーは弱いモデルでは連続、強いモデルでは最終ゲート1回」へ収束した。

### 欠けていた設計原則が出た（P9）
Anthropic harness-design 記事の鍵語（日本語スカウト経由で発見）:
**「ハーネスの各要素はモデルができないことの仮定」**
→ ハーネスの各部品は「モデルにこれができない」という**期限付きの賭け**である。
モデルが良くなれば賭けは外れ、部品はコストだけになる。
これが日本語圏の解体記録5件（特に奥山「モデルの進化との付き合い方」）と
Jain のフロンティア結果を**1文で説明する**。

→ **P9: ハーネスの各部品は、自分が前提している「モデルの不足」を明示し、
個別に無効化できること。** 賭けが外れたら外せる形で作る。

### 止めた理由（imozuru の停止基準）
- 要る主張 C1-C6 すべてに原文の場所が付いた（C6のKastnerは一次取得済・P8は診断のみに格下げ）
- 独立2経路（英/日）の報告が、同一の中核文献（Anthropic harness系・Jain・MAST・HypoSearch系）へ収束
- かつ**設計を反証する側の証拠も揃った**（Jain・コキエ・2608.16801・Carlini・解体記録5件）
→ これ以上掘るより、未測定領域（hook強制 vs プロンプトのみ）を**測れる形で作る**方が得られるものが大きい

### ユーザー判断: 階層別センサーは採用(1)。ただし Fable は優先度低
原文「1で良いですが現状Fableのパフォーマンスは良くないので優先度は低くなるかと思います」
→ 設計帯を引き直す: haiku/sonnet=連続センサー / opus=最終ゲート1回 / fable=opusと同扱い・検証対象外。
根拠との整合: Jain で素で初回成功したのは Sonnet 4.6・Opus 4.6・Gemini 3.8 Flash であり、
3/10→10/10 を稼いだのは**低コストモデル**。Anthropic が sprint を捨てたのも Opus 4.6。
よってハーネスが元を取る帯は haiku/sonnet。Jen は18体中12体が sonnet なので投資先と実稼働が一致する。

### P9 の自己適用（記録）
v3 の看板「指揮は Fable」は、P9 の言う「モデルの不足に対する期限付きの賭け」そのもの。
「Fable は長時間一貫性で強い」という賭けで建てた構造が、ユーザーの実測では配当を出していない。
日本語圏の解体記録5件と同じ形。今回は倒さないが、P9 の最初の適用対象として記録する。
