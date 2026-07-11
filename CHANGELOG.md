# Changelog

## v3.5.0 (2026-07-08) — Ratio Guard（jenのみ、jen-classicは対象外）

手動運用で観測された呼び出し比率 sonnet:opus:fable ≈ 20:4:1 を、
狙っていた分布として明文化し、自己改善ループ（v3.1）の記録から
実測できるようにした。

### 追加（jen edition のみ。jen-classicはFableを使わないため対象外）
- **目標分布の明文化**: `references/model-tiering.md` に「目標分布」
  （sonnet 80% / opus 16% / fable 4%、コスト按分約67/22/11%）を追加
- **architect を opus のまま維持する根拠を明記**: fable昇格案は検討したが、
  fableへ動かすとfableの呼び出しシェアが目標の2倍以上に膨らみ実測比率と
  乖離するため不採用（採用しなかったもの、として記録）
- **Ratio Guard 自己点検**: `.jen/routing-stats.json` から実測比率を集計し
  目標分布との乖離を検知。sonnet:opus < 3:1 で昇格しすぎ疑い、
  opus:fable < 2:1 でdeep-solver多用/classifierフォールバック疑いを
  `.jen/decisions.md` へ一行記録（強制停止はしない、自己点検のみ）
- **`/jen:jen-status` 拡張**: `jen_status.py` が routing-stats.json を集計し
  sonnet:opus:fable の実測比率と目標との差分を表示する

### 採用しなかったもの
- architect の fable 昇格 — 実測比率と乖離するため見送り（上記参照）
- 比率逸脱時のhooksによる強制停止 — v3.4と同じ理由（数値ベースのhard-stopは
  プラグインからの計測が不正確になりやすい）で自己点検止まりに統一

## v3.4.0 (2026-07-07) — ループガード＆コンテキスト衛生

2026年のループエンジニアリング知見（無進捗検知、外側ループリセット、
plan churn、コンテキスト衛生、graceful failure）から、Jen未実装のものを採用。

### 追加（jen / jen-classic 共通）
- **無進捗検知（サーキットブレーカー）**: 同一アプローチ2回目=STUCK、
  台帳2サイクル無変化でブレーカー作動。判定は台帳差分で機械的に（自己申告不採用）
- **外側リセット**: ブレーカー時はステップ再試行ではなくタスク分解から戦略を
  引き直す（Magentic-One型dual-loop）。1ミッション2回まで、3回目はHuman Gate
- **空転検知**: 実行を伴わない再計画は2回まで。3回目は最小タスク強制実行
- **コンテキスト衛生**: 最小コンテキスト委譲 / workerからは結論＋証跡パスのみ回収
  （生ログは.jen/logs/へ外部化）/ 重要ルール・決定はcompactionに頼らず台帳へ
- **graceful failure報告**: どの停止でも「達成分・未達理由（確定/推測）・
  回復アクション」の3点報告を義務化。無言停止禁止

### 採用しなかったもの
- 数値ベースのbudget hard-stop自動化 — hooksでの強制はトークン計測が
  プラグインからは不正確になりやすい。台帳ベースの回数上限で代替

## v3.3.0
## v3.3.0 (2026-07-06) — 教訓台帳（過ちを繰り返さない）

### 追加（jen / jen-classic 共通）
- **`.jen/lessons.md`**: 失敗が解決されるたび、事象 / 考察（確定・推測・未確認を
  区別）/ 解決策 / 再発防止ルール（1行命令形）を記載する教訓台帳
- **委譲前の教訓注入**: PMOがtask_type・失敗タイプの一致する再発防止ルール
  （最大3件、ルール行のみ）を委譲promptへ自動で含める
- **再発検知**: verifierが既存ルール違反の失敗に `[再発:L-xxx]` をタグ付け。
  再発はボードに⚠️表示され、該当ルールは以後の委譲promptの先頭に固定。
  2回目の再発で教訓自体を見直す
- repair / deep-solver に教訓記載を義務化。根本原因未特定のまま閉じることを禁止
- board.md の解決済み失敗に教訓ID（L-xxx）を紐づけ

## v3.2.0-classic
## v3.2.0-classic (2026-07-06) — Classic Edition 追加

Fableを使わない `jen-classic` プラグインを同梱（機能はv3.2.0と同一、モデル階層のみ変更）。

### Fable版との差分
- PMO / deep-solver: fable → **opus**（メインセッションも /model opus）
- Fableの長時間耐性を構造で補償:
  **再アンカリング**（委譲毎にmission.md読み直し）/ **1サイクル=1タスク厳守** /
  **セッションローテーション**（8サイクル毎にhandoff→新セッション）
- 最終昇格は **opus合議制**: architect と debugger が独立仮説（互いの出力を見せない）
  → deep-solver が矛盾判定・統合。単独モデルの思い込みを相殺
- コスト: Opusは Fableの約半額のため、合議（opus×3）でもfable単独昇格と同水準
- ⚠️ jen と jen-classic は agent名が同一のため**同時有効化禁止**

## v3.2.0
## v3.2.0 (2026-07-05) — 可視化プロトコル

「誰が・何を・失敗はどう引き継がれたか」をユーザーに見せる。

### 追加
- **やり取り行**: 委譲・完了・REJECT・昇格・Human Gateを社員間のやり取りとして
  1行フォーマットで必ずチャットに表示（`🔍 jen-verifier ✖ REJECT[format] ▶ jen-builder ...`）
- **ワークボード** `.jen/board.md`: 進行中テーブル / やり取りログ /
  失敗共有（未解決・解決済み）。イベント毎にPMOが更新
- **`/jen:jen-board` コマンド**: 現在のボードと次に起きるイベントを表示
- **verifierの「共有」欄**: REJECT時に失敗要約・引き継ぎ先・再発防止観点を必ず出力
- **規律**: 沈黙禁止（イベント発生順に表示）/ 隠蔽禁止（失敗を薄めない）/
  冗長禁止（やり取り行は1行、詳細はboard.mdへ）

## v3.1.0
## v3.1.0 (2026-07-05) — 自己改善ループ

SNSで共有されていた自己改善型エージェント設計の知見から、Jenの設計思想
（PMO型 / Fable指揮 / 昇格ラダー / Human Gate）と整合する4要素のみを蒸留して採用。

### 追加
- **ルーティング学習**: タスク完了ごとに `.jen/routing-stats.json`（JSONL）へ
  担当×検収結果を記録し、PMOが担当割当・昇格判断の参考にする
- **失敗分類**: verifier / strict-verifier が REJECT 時に失敗タイプ
  （hallucination / format / drift / tool_failure / cost）をタグ付けし、
  repair・deep-solver昇格時の失敗履歴として引き継ぐ
- **ドリフト監視**: longrun の checkpoint 毎に mission.md との整合を1行自己評価。
  逸脱検出時はサイクルを止めて再プランニング
- **スキル候補の提案**: 同種タスク3回以上ACCEPTでパターンを
  `.jen/skill-candidates.md` に抽象化して提案。**skills/への昇格は人間承認必須**
- 雛形追加: `templates/memory/routing-stats.jsonl.example`, `skill-candidates.md`

### 採用しなかったもの（理由つき）
- permissions skip 等の安全緩和 — Human Gate設計と矛盾
- スコア閾値による数値品質ゲート — LLM自己採点は疑似精度になりやすく、
  ACCEPT/REJECT二値＋理由の方が検収として堅い
- スキルの完全自動生成 — 公開プラグインで自己生成プロンプトが無検証に
  増殖するのは事故のもと。提案止まりに変更

### 不変条件
昇格ラダー（haiku→sonnet→opus→fable）・deep-solver直行禁止・Human Gate・
外部通信なしは v3.0 から変更なし。

## v3.0.0 (2026-07-02) — Fable Edition
- 初回公開。詳細は README を参照
