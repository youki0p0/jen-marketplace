# Jen v3.2 Visibility Protocol — 社内のやり取りをユーザーに見せる

目的: ユーザーが「誰が・何を・どうなったか」を追えるようにする。
委譲・完了・失敗・昇格は社員同士のやり取りとして必ず可視化する。

## 1. やり取り行（チャット表示・必須）

PMOは以下のイベント発生時、ユーザー向け出力に**必ず1行**含める:

```
🎼 jen-pmo ▶ jen-builder     T-014「ログイン画面実装」を委譲 | AC: 空状態/エラー状態あり
🔨 jen-builder ✔ 完了 ▶ jen-verifier   T-014 検収を依頼
🔍 jen-verifier ✖ REJECT[format] ▶ jen-builder   差し戻し: エラー状態のUIが未実装
⬆️ jen-pmo ▶ jen-debugger    T-014 昇格(REJECT2回) | 失敗履歴: format×2 を添付
🧑 jen-pmo ⏸ Human Gate      T-020 本番deployは承認待ち
```

書式: `絵文字 送り手 動作 ▶ 受け手  タスクID「内容」 | 補足`
- 動作: 委譲 / 完了 / REJECT[失敗タイプ] / 昇格 / Human Gate / 保留
- 失敗時は**理由の要約と、誰に何を引き継いだか**を省略しない
- 絵文字目安: 🎼pmo 🔎scout 📚research 🔨builder 🎨frontend 🧪test
  🏛architect 🐛debugger 🔍verifier 🛡strict-verifier 🚀release 🧠deep-solver

## 2. ワークボード（.jen/board.md・毎イベント更新）

PMOがやり取り行を出すたびに `.jen/board.md` も更新する:

- **進行中テーブル**: Task / 内容 / 担当 / 状態(WIP・検収中・差し戻し・昇格・完了) / 最終イベント時刻
- **やり取りログ**: 最新15件のやり取り行（古いものは .jen/logs/ へ）
- **失敗共有（未解決）**: REJECT内容・失敗タイプ・現在の引き継ぎ先。
  解決したら「解決済み」へ移し、何が原因でどう直したかを1行残す

## 3. 表示の規律

- 沈黙禁止: 3タスク以上を連続処理する場合も、まとめてではなく
  イベント発生順にやり取り行を出す
- 隠蔽禁止: 失敗・昇格はユーザーが最も知りたい情報。要約で薄めない
- 冗長禁止: やり取り行は1行厳守。詳細は board.md と verification.md へ
- longrunでは checkpoint 毎に board.md の進行中テーブルを handoff.md にも転記
