# Changelog

## v3.7.2 (2026-08-28) — 全体監査による修正（jen / jen-classic 共通）

多角的な棚卸しで見つかった20件を修正。うち2件はv3.7.0/v3.7.1で作り込んだ自傷バグ。

### 🔴 実行を壊していたバグ
- **scoutにBash権限が無いのに `echo $CLAUDE_PLUGIN_ROOT` を指示していた**
  （v3.7.1の自傷）: scoutの`tools:`は Read/Write/Edit/Grep/Glob。skillmap機能は
  起動時点で失敗していた。→ **依頼元（PMO / jen-auditコマンド）がプラグインルートを
  解決してpromptで渡す**方式に変更（scoutをread-onlyのまま保つ）
- **jen-classic のコマンド名前空間が全て `/jen:`** だった（正しくは `/jen-classic:`）。
  Classic利用者が叩いても存在しないコマンドを案内していた。6箇所修正

### 🟠 記述が事実と異なっていた
- `plugins/jen-classic/README.md` が Fable版のコピーで「jen-pmo は model: fable」と
  記載（実際は opus）。Classic の存在意義と正反対だったため全面改訂
- jen-classic の `plugin.json` keywords に `fable` が残存 → `no-fable` へ（marketplace.json と整合）
- jen-classic の `jen-deep-solver.md` が昇格ラダーを「→ **fable**」と記載 → 「→ **opus合議**」
- jen-classic の SKILL.md 参照ラベルが「モデル階層(Fable構成)」→「(Classic/Opus構成)」
- 共通化した `behavior-audit.md` が、Classicに存在しないRatio Guardを監査軸にしていた
  → エディション中立な「ルーティング記録の整合性」に変更
- `plugins/jen/README.md` のコマンド一覧が3本のまま（実際は5本、jen-board/jen-audit欠落）
- marketplace.json の jen 説明に commands 本数を追記
- CHANGELOG の見出し4重複（v3.3.0 / v3.2.0-classic / v3.2.0 / v3.1.0）を解消
- v3.6.0〜v3.7.1 の日付が実際のコミット日とずれていた（08-25 → 08-28）

### 🟡 設計上の欠陥（分析の誤り）
- **Ratio Guard の測定定義が目標定義と食い違っていた**: `routing-stats.json` は
  1タスク完了につき委譲**先**のmodelを1行記録する。PMO(fable)は委譲**元**なので
  記録されず、統計上の`fable`は実質 deep-solver のみ。にもかかわらず
  v3.5は「PMOを含む全体比率20:4:1」と同一視し「opus:fable ≈ 4:1 が健全」と記載していた。
  委譲先ベースで4:1は「opusタスク4件に1件deep-solver発火」＝最終手段の常用という
  異常事態を意味する。→ 測定できるもの/できないものを明記し、閾値を
  **10:1未満=要注意 / 4:1未満=異常**へ訂正。`jen_status.py` も同期
- **agent frontmatter の `effort`/`memory`/`isolation`/`color` はサポート未検証**である旨を明記。
  無視されている場合 `isolation: worktree`（6 agents）は分離しておらず、
  **分離を前提にした安全設計をしないこと**を注意書きとして追加

### 🟢 安全性・移植性
- **`.jen/logs/` への平文ログによるsecret露出リスクをREADMEに明記**。
  `post_tool_log.py` は全ツールペイロードをそのまま追記するが、プラグインは
  利用者の`.gitignore`を書き換えない。「同梱」という誤解を招く記述を訂正し、
  `echo '.jen/' >> .gitignore` を導入直後の必須手順として明示
- **force pushガードの穴を塞いだ**: `git push -f`（短縮形）、`-uf` 等の
  フラグ結合、`+refspec` 形式が素通りしていた。誤検知テスト（`-u`, `--tags` 等）も実施
- `jen_quality_gate.sh` の `npm test -- --runInBand` は Jest 固有で
  vitest等では失敗するため除去
- テンプレ名 `routing-stats.jsonl.example` → `routing-stats.json.example`
  （実行時ファイル名 `.jen/routing-stats.json` と統一）

### 検出可能にした既知の設計課題（構造変更は保留）
- `skills/jen/SKILL.md` と `agents/jen-pmo.md` が**同じPMO規律を二重定義**しており
  手動同期が必要（実際にドリフト実績あり）。統合するかは設計判断のため保留し、
  スキルマップ整合性チェックの「必ず見る既知のドリフト源」に登録して
  検出できるようにした

## v3.7.1 (2026-08-28) — Skill Map パス修正 + 利用可能スキル一覧トリガー（jen / jen-classic 共通）

CLAUDE.mdへの記載でトリガーする案は不採用にした（下記）。代わりに、
v3.7.0のスキルマップ設計に実際のバグがあったので修正し、正しい
仕組み（skill descriptionによる自動トリガー）で同等のことを実現した。

### 修正
- **skillmap.jsonの棚卸しパスが壊れていた**: v3.7.0は
  `plugins/jen/agents/*.md` のようなJenソースリポジトリ相対のパスを
  前提にしていたが、実際にプラグインとしてインストールされた場合、
  実体は `~/.claude/plugins/cache/...` 配下にあり、ユーザーの
  プロジェクトcwdからは見えない。scoutがまず `$CLAUDE_PLUGIN_ROOT` を
  解決し、そこからの絶対パスで棚卸しするよう修正。解決できない場合は
  「未解決のため未実施」と明記し、誤った場所を黙ってスキャンしない
  （Jenのソースリポジトリ自身を編集する場合はリポジトリ相対パスのままでよい）

### 追加
- **利用可能スキル一覧への応答**: `skills/jen/SKILL.md` の`description`に
  「Jenで使えるスキル/エージェント一覧」を尋ねる質問を追記し、そのトリガー
  でscoutにskillmap.jsonを構築/参照させてから回答する（記憶やREADMEの
  記憶で答えない）。CLAUDE.mdではなくskillのdescriptionで実装した理由は
  下記。

### 採用しなかったもの
- **CLAUDE.mdへの記載**: 当初の依頼どおりCLAUDE.mdを検討したが、
  公式ドキュメントで「プラグイン自身のCLAUDE.mdはプロジェクトコンテキスト
  として読み込まれない」と明記されており、かつプラグインが
  インストール先ユーザーのCLAUDE.mdへ自動的に書き込む仕組みも存在しない
  （常に人間の手動編集）。「特定の質問でこのagentを起動する」という
  トリガー制御は公式にはskill/agentの`description` frontmatterの役割
  であるため、そちらで実装した。

## v3.7.0 (2026-08-28) — Skill Map & Behavior Audit（jen / jen-classic 共通）

これまでJenには成果物(内容)を監査する担当（verifier/strict-verifier/
security-reviewer等）はいたが、PMOの行動そのものを監査する担当がいなかった。
Ratio Guard・ループガード・可視化プロトコルの自己点検はすべてPMOの自己申告
（board.md/routing-stats.json）に依存し、独立した第三者チェックが無かった。
コードマップ担当のjen-scout(haiku)に、この2つの役割を兼務させた。

### 追加（jen / jen-classic 共通）
- **スキルマップ `.jen/skillmap.json`**: agents/skills/commands/referencesの
  棚卸しと整合性チェック（SKILL.mdのルーティング表漏れ、model-tiering.mdと
  agentファイルの`model:`不一致、存在しないreferenceへのリンク等を検出）
- **行動監査 `.jen/audit.md`**: `.jen/logs/tool-events.jsonl` /
  `.jen/logs/stop-events.jsonl`（PostToolUse/Stop hookが機械的に記録する、
  LLMの協力に依存しない実ログ）を、board.md/routing-stats.json/decisions.md
  （PMOの自己申告）と突き合わせ、可視化コンプライアンス・Ratio Guard整合性・
  コンテキストスコープ遵守・ループガード遵守を 準拠/逸脱(証跡付き)/判定不能
  の3値で報告する
- **`/jen:jen-audit` コマンド**: ユーザーがPMOを介さず直接scoutへ監査を
  依頼できる独立チェック経路（PMOがcheckpoint毎の依頼自体を怠った場合の
  唯一の対抗策）
- 新規リファレンス: `references/behavior-audit.md`

### 採用しなかったもの / 正直な限界
- 逸脱検知時の自動修正・自動停止 — v3.4〜v3.6と同じ理由でhard-stop
  自動化はせず、報告のみに留める
- 「PMOの戦略判断が妥当だったか」の価値判断 — haiku・構造的な突き合わせが
  前提のため、それはverifier/strict-verifier/人間の領分とし持たせない
- PostToolUseペイロードの正確なスキーマ（Task委譲prompt本文が含まれるか等）
  はClaude Codeハーネス依存であり独自検証していない。取得できた範囲でのみ
  判定する旨をbehavior-audit.mdに明記した

## v3.6.0 (2026-08-28) — Context Scoping（jen / jen-classic 共通）

[NanoNets/Graft](https://github.com/NanoNets/Graft)（SWE-bench Verified で
resolve率 54%→66%＋ツール呼出/トークン/時間を削減したと報告されている、
「毎回リポジトリを読み直す代わりに永続コードマップを差分更新して使い回す」
手法）にヒントを得て、jen-scout(haiku)の役割を拡張した。

### 追加（jen / jen-classic 共通）
- **永続コードマップ `.jen/codemap.json`**: ファイル→役割/主要シンボル/
  依存関係の軽量マップ。scoutが初回はフルスキャンで構築し、以降は
  変更されたファイルとその隣接ノードだけ差分更新する（全体再構築はしない）
- **委譲前のローカライズ必須化**: コードを読み書き/検収する担当
  （builder/frontend/test/architect/debugger/verifier/strict-verifier/
  security-reviewer/ux-critic）への委譲前に、scoutがcodemapを参照して
  対象ファイルを絞り込み、その結果のみを委譲promptへ渡す
  （「リポジトリ全体を読んで」と指示しない）
- **エスケープハッチ**: 委譲先がスコープ不足を発見したら自分で拡張してよい
  （ループガードの空転検知の対象外）。作業後はscoutが差分更新する
- 新規リファレンス: `references/context-scoping.md`

### 採用しなかったもの
- Graft自身の実測値（-42%トークン/-60%時間/+12pt正解率）をJenの成果として
  そのまま謳うこと — Graft自体の計測値であり、Jenのマルチエージェント構成
  への移植効果は独自に検証していないため、`context-scoping.md`に
  「効果不明な部分」として正直に明記するに留めた
- codemapの鮮度を数値で強制すること — v3.4/v3.5と同じ理由で、
  hard-stop自動化はせずエスケープハッチでの自己修復に委ねる

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
