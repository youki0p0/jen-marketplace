# Changelog

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
