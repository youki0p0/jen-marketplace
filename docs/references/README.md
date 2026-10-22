# References

Jen の設計・運用で参照する外部資料。

## kastner-2007-horizon-estimation-stopping-rule.pdf

Kastner M, Straus S, Goldsmith CH. *Estimating the Horizon of Articles to Decide When to Stop Searching in Systematic Reviews: An Example Using a Systematic Review of RCTs Evaluating Osteoporosis Clinical Decision Support Tools.* AMIA Annu Symp Proc. 2007:389–393. PMCID: PMC2655834 / PMID: 18693864

### 要点

- 系統的レビューの文献検索には「いつ検索をやめるか」の合理的ルールがない、という問題提起。
- 生態学の capture-mark-recapture (CMR) を応用し、複数DBの重複捕捉パターンから「まだ見つかっていない件数」を Poisson 回帰で推定し、全体数（Horizon）を 95% 信頼区間つきで求める。
- MEDLINE → EMBASE → CINAHL → EBM Reviews の順に4DBで検証。既知 1,246 件に対し Horizon 推定 1,838 件（95% CI 1,749–1,955）、捕捉率は約 68%。
- 前向きに使えば「既知件数が Horizon の CI に入ったら停止」という停止ルールになり、検索順序の最適化にも使える。
- 限界：後ろ向き検証のみ、算出タイミング（スクリーニング前/後）で結果が変わり得る、停止の閾値は未確立。

### Jen での使いどころ

research / conduct モードの調査タスクで、「複数ソースを順に当たる際の打ち切り判断」や「取りこぼし件数の見積もり」を設計する際の参考。
