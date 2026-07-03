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
