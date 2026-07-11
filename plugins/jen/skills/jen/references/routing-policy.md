# Jen v3 Routing Policy

## 優先順位

1. Human Gateに該当するなら停止。
2. read-onlyで足りるならscout/research/reviewerを使う。
3. 通常実装はbuilder/frontend。
4. テストはtest。
5. 不明バグはdebugger。
6. 難設計はarchitect。
7. 完了候補はverifier。
8. 高リスクはstrict-verifier。
9. opus層が失敗した問題のみdeep-solver（fable）。

## ルーティング学習（v3.1）

担当割当の前に `.jen/routing-stats.json` を参照する（存在すれば）。
- 同種タスクで同一担当のREJECTが2回以上 → 別担当または上位ティアを優先
- 統計は参考情報。昇格ラダーの順序・deep-solver直行禁止・Human Gateは上書きしない
- 記録はPMOが1タスク完了ごとにJSONL形式で1行追記する

## Ratio Guard 自己点検（v3.5）

longrun の checkpoint 毎、または conduct/route で20タスク処理毎に、
`.jen/routing-stats.json` から sonnet:opus:fable 比率を集計し
`references/model-tiering.md` の「目標分布」（約20:4:1）と比較する。
乖離を検知したら `.jen/decisions.md` に一行残し、次の委譲判断に反映する
（強制停止はしない）。詳細: `model-tiering.md`

## 昇格（haiku → sonnet → opus → fable）

- scoutで不足 → research or builder
- builder失敗 → debugger or architect
- frontend失敗 → test/ux-critic/debugger
- test失敗 → debugger
- verifier REJECT 1回 → 該当担当へ差し戻し
- verifier REJECT 2回 → opus系（architect/debugger）へ昇格
- verifier REJECT 3回 or opus層失敗 → jen-deep-solver（fable）へ昇格
- deep-solver失敗 or strict-verifier REJECT → Human Gate

deep-solver呼び出し時は、それまでの失敗履歴（試した修正・REJECT理由）を
必ずpromptに含める。含めないと同じ探索を繰り返しコストを倍払う。

## 並列化してよい条件

- 依存がない。
- 同じファイルを触らない。
- 片方の出力がもう片方の仕様を変えない。
- 失敗しても安全に戻せる。

## 並列化しない条件

- 同じコンポーネント/型定義/APIを触る。
- DB schemaやauthに関係する。
- 仕様がまだ揺れている。
- テストが存在せず検証不能。

## nested subagents（v3新設）

builder/architect/debuggerは自分専用のread-only scout（haiku）のみ
子として起動してよい。実装系の再委譲はPMOへ返す。
詳細: `model-tiering.md`
