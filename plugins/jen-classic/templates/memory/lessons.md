# Lessons — 教訓台帳

失敗の考察と解決策。委譲前にPMOが該当ルールを注入する。
書式は references/lessons-protocol.md を参照。

## L-001 [tool_failure] （記入例）npm testがCI環境変数不足で失敗
- 事象: T-009でテストが常時失敗。ローカルでは再現せず
- 考察(根本原因): CI環境に DATABASE_URL 未定義（確定）。他env不足の可能性（推測）
- 解決策: env.example追加＋CI設定にsecrets注入
- 再発防止ルール: テスト系タスクの委譲時は env.example と CI設定の環境変数を先に確認する
- 適用範囲: task_type=test,debug / 関連: T-009 / 再発: 0回
