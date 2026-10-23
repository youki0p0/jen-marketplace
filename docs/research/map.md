# map: agent-orchestration-harness

問い: LLMエージェントのオーケストレーション／ハーネスを2026年現在に設計するとき、
何が実証的に有効で、どこで失敗すると 測定されているか。プロンプト主体の
オーケストレータ（Jen v3.8.2 相当）に対し、決定論的なハーネスはどこまで担うべきか。
最初の検索語: LLM agent orchestration harness / multi-agent failure modes

## 要る主張
- [ ] C1【場】この分野の知見はどこに集まっているか（学会・arXiv・企業のエンジニアリングブログ・リポジトリ・一覧） —
- [ ] C2 Anthropic 自身の一次情報は、マルチエージェント／ハーネス設計について何を言っているか（効果の数字つき） —
- [ ] C3 Sakana AI の論文・記事は、エージェント構成・進化・自己改善について何をどれだけ動かしたと報告しているか —
- [x] C4 マルチエージェントが単一エージェントに**負ける**条件は何か。原因として何が測定されているか —
  - `sources/arxiv-2609.01294-explore-before-committing.txt` L23-34「they often search along a single evolving trajectory」「subsequent tool calls tend to reinforce the same path」
  - `sources/arxiv-2602.03304-to-search-or-not.txt` L35-40「over-search (redundant searching despite sufficient knowledge) and under-search (premature termination yielding incorrect answers)」/ L33-34「outcome-centric training that prioritize final results over the search process itself」
  - `sources/arxiv-2608.02009-halt.txt` L22-24「a 3B Self-Ask agent runs to its search budget on 78–88% of questions instead of halting on its own」
- [x] C5 決定論的なハーネス（足場）が担って効果が出た部分はどこか。逆に何が足りないままか —
  - `sources/arxiv-2608.02009-halt.txt` L49-52「without retraining or modifying the host agent」/ L25-27「We frame stopping as evidence coverage rather than generator confidence」/ L28-30「HALT stops only when cumulative evidence supports each required claim」/ L42-45「driven by claim–evidence alignment rather than generic sufficiency, fixed stop positions, or lexical overlap」/ L45-47「HALT abstains when coverage cannot be reliably verified」
  - `sources/arxiv-2609.01294-explore-before-committing.txt` L40-44「generates lightweight hypotheses as soft search hints, explores them through bounded independent branches, and compares branch-level evidence before commitment」/ L48-51「improving Qwen3.5-122B from 46.7 to 60.0 on BC-small while using fewer tool calls than five independent trajectories」（※ツール数の比較対象は5本独立試行／Majority。単一試行より少ないとは書いていない・L368）
  - 足りない部分: `arxiv-2602.03304` の DAS は**学習側**の介入（preference dataset）でハーネスでは再現できない — L41-46
- [~] C6 上記の「定番のやり方」の元になった原典・研究はあるか —
  - 早すぎる要約が探索を妨げる（＝原文を要約せず渡す根拠）: `sources/kuhlthau-1991-inside-search-process.txt`（Kuhlthau 1991）
  - 問いは探すうちに変わる／たどり方の6つの動き: `sources/bates-1989-berrypicking.txt`（Bates 1989）
  - 飽和を独立2経路の重なりで見積もる（capture-recapture）: Kastner ら 2007 — **未取得**（PMC で captcha。別の置き場を探す）
  - 情報採餌理論 Pirolli & Card 1999 — 有料（DOI 10.1037/0033-295x.106.4.643）・未取得

## 用語

## 人

## 場

## 原文（sources/）
| 論文・資料 | ファイル | 元の URL | どこから来たか（周・動き） |
|---|---|---|---|
| 〔論文〕HALT: Verification-Aware Stopping for Retrieval-Augmented Search Agents (Roh & Han 2026) 測定あり | `arxiv-2608.02009-halt.txt` | https://arxiv.org/pdf/2608.02009 | 0周・親がimozuruのtheory.mdから（後ろへ） |
| 〔論文〕To Search or Not to Search: Aligning the Decision Boundary of Deep Search Agents via Causal Intervention (Zhang ら 2026, WWW'26) 測定あり | `arxiv-2602.03304-to-search-or-not.txt` | https://arxiv.org/pdf/2602.03304 | 同 |
| 〔論文〕Explore Before Committing: Hypothesis-Guided Search for Deep Research Agents (Zhou ら 2026, HypoSearch) 測定あり | `arxiv-2609.01294-explore-before-committing.txt` | https://arxiv.org/pdf/2609.01294 | 同 |
| 〔論文〕Inside the Search Process (Kuhlthau 1991) | `kuhlthau-1991-inside-search-process.txt` | https://tefkos.rutgers-sci.domains/Courses/612/Articles/Kuhlthau_Inside_91.pdf | 同 |
| 〔論文〕The design of browsing and berrypicking techniques (Bates 1989) | `bates-1989-berrypicking.txt` | https://www.pages.gseis.ucla.edu/faculty/bates/articles/berrypicking.pdf | 同 |

## 次の手がかり
- Kastner ら 2007: 4箇所すべてボット対策で届かず（log.md参照）→ **ユーザーにブラウザで開いてもらう**
- [済] HALT の測定条件: Self-Ask 3B・予算8ループ・2Wiki/HotpotQA/MuSiQue。過少探索は7Bで51/64/79% (L339-343)
- [済] HypoSearch の分岐判定は LLM（Branch Detector・プロンプト全文 L802-845）。予算管理のみ決定論
- Anthropic / Sakana AI の一次情報（検索役2本の報告待ち）
- `arxiv-2602.03304` の DAS リポジトリ https://github.com/Applied-Machine-Learning-Lab/WWW2026_DAS （未確認）
