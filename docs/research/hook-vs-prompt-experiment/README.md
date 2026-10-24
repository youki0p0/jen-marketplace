# hook-vs-prompt-experiment

同じ規則を「hook で強制する」場合と「プロンプトで指示するだけ」の場合を比べた実験の、一式と記録である（2026-10-24〜25）。

**結果と考察は `findings.md` にある。まずそちらを読む。** この README には、ファイルの説明と再現のしかただけを書く。

## ファイル

| パス | 中身 |
|---|---|
| `findings.md` | 結果と考察。先行研究の再調査、設計、結果、Jen v4 への示唆、限界、次の実験 |
| `results-main.md` | 本番180回の集計表（`summarize_main.py` の出力） |
| `results-pilot.md` | 試行版18回の集計表（`summarize.py` の出力） |
| `make_tasks.py` | 課題 C_money・D_dates・E_report・F_invoice_ok を生成する。A_invoice・B_slugify は手で書いた |
| `tasks/<課題>/repo/` | エージェントに渡る中身（README の仕様、`src/` の雛形、`tests/`） |
| `tasks/<課題>/hidden/test_spec.py` | 隠し仕様テスト。エージェントには見せない |
| `tasks/<課題>/reference.py` / `cheat.py` | 参照解と、ごまかした解の例（課題の検証用） |
| `conditions/prompt_main.txt` | 本番の指示文（P0 と H で共通） |
| `conditions/prompt_base.txt` | 試行版の指示文（圧力の一文なし） |
| `conditions/prompt_p1_suffix.txt` | P1 で足す証拠契約 |
| `conditions/H_claude/` | H の作業場所に `.claude/` として置く hook |
| `run.py` | 1回を実行する。作業場所を作り、開始時のハッシュを取り、`claude -p` を起動する |
| `judge.py` | 1回を機械判定する。エージェントの自己申告は使わない |
| `claims.py` | 最終報告の主張を分類する（v2。sonnet、根拠の逐語引用が必須） |
| `validate_claims.py` | 分類器を正解付き27件で確かめる |
| `batch_main.py` | 本番のバッチ。再開できる |
| `summarize_main.py` | 本番の集計 |
| `batch.sh` / `summarize.py` | 試行版のバッチと集計 |
| `runs/` | 試行版の記録。`A_invoice_H_r0` は通し確認で、集計に入れていない |
| `runs_main/{haiku,sonnet}/<課題>_<条件>_r<回>/` | 本番の記録 |

各回のディレクトリには次のファイルがある。

| ファイル | 中身 |
|---|---|
| `meta.json` | 条件・モデル・指示文・起動コマンド・終了コード |
| `baseline.json` | 開始時の全ファイルのハッシュ |
| `transcript.jsonl` | `claude -p --output-format stream-json` の記録 |
| `hooklog.jsonl` | hook の判断の記録（H のみ） |
| `judge.json` | 機械判定の結果 |
| `claims.json` | 主張の分類 |
| `work/` | 終了時の作業場所 |

## 記録について、置くときに変えたこと

- 各回の `work/.git` は除いた（入れ子のリポジトリになるため）。判定は `.git` を見ないので、判定器は置いた状態でそのまま動く。置いた状態で全199回を再判定し、元の `judge.json` と一致することを確かめた。
- `transcript.jsonl` から `stream_event` の行（ストリーミング途中の差分）を除いた。完成したメッセージと内容が重複しており、容量の約75%を占めていた。判定器はこの行を読まない。
- 記録に出てくる `/tmp/claude-0/...` の絶対パスは、実験を走らせたセッションの作業場所である。
- 試行版の `claims.json` は v1 の分類器（haiku、引用なし）で作ったもので、否定文の誤読がある（`findings.md` 3.4）。本番では使っていない。

## 再現のしかた

必要なもの: Claude Code（2.1.310 で実行した）、Python 3、pytest。

```
cd docs/research/hook-vs-prompt-experiment
python3 make_tasks.py                      # 課題を作り直す（作り直さなくても tasks/ にある）
python3 run.py C_money H 1 --model haiku --out runs_try   # 1回だけ試す → runs_try/haiku/C_money_H_r1/
python3 judge.py runs_try/haiku/C_money_H_r1
python3 claims.py --model sonnet runs_try/haiku/C_money_H_r1
python3 batch_main.py --out runs_rerun --parallel 4 --reps 5   # 本番と同じ180回を別の場所へ
python3 summarize_main.py --root runs_rerun
```

注意点:

- `run.py` は、同じ名前の回が既にあると上書きを拒否する。置いてある本番の記録（`runs_main/`）とぶつからないように、新しく走らせるときは `--out` で別の場所を指定する。
- `run.py` は `--setting-sources project` で起動するので、利用者の `~/.claude` の設定は読まない。組み込みプラグインは外せない（`findings.md` 3.5）。
- `run.py` の `DROP_ENV` は、実験を走らせたクラウド環境に固有の環境変数を子に渡さないためのものである。手元のマシンでは、該当する変数が無いだけで害は無い。
- Jen の hook で測るときは、`conditions/H_claude/` を差し替える。`judge.py` は hook の中身に依存しないが、保護対象への書き込み試行の検出には `conditions/H_claude/hooks/guard.py` の正規表現を流用しているので、残しておくか、`judge.py` の import を書き換える。
