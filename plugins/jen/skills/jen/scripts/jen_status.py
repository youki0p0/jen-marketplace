#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import json

paths = ['.jen/mission.md', '.jen/tasks.json', '.jen/verification.md', '.jen/handoff.md']
for p in paths:
    path = Path(p)
    print(f"\n## {p}")
    if path.exists():
        text = path.read_text(encoding='utf-8')
        print(text[-4000:])
    else:
        print('(missing)')

# Ratio Guard (v3.5, v3.7.2で解釈を訂正): .jen/routing-stats.json は
# 1タスク完了につき1行、その「委譲先」のmodelを記録する。PMO(fable)は委譲元なので
# 行にならず、統計上の fable は実質 deep-solver のみ。つまりこれは指揮を含む
# 全体比率(20:4:1)ではなく「委譲先の分布」を測っている。
# 詳細: references/model-tiering.md「測定できるものと、できないもの」。強制はしない。
stats_path = Path('.jen/routing-stats.json')
print(f"\n## Model Mix ({stats_path})")
if stats_path.exists():
    counts = Counter()
    for line in stats_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        model = entry.get('model')
        if model:
            counts[model] += 1

    sonnet, opus, fable, haiku = (counts.get(m, 0) for m in ('sonnet', 'opus', 'fable', 'haiku'))
    print(f"委譲先の分布: sonnet={sonnet} opus={opus} fable={fable} haiku={haiku}")
    print("※ PMO(fable)は委譲元のため未計上。fable=deep-solverの発火回数。")

    if opus:
        so = round(sonnet / opus, 1)
        print(f"sonnet:opus = {so}:1  (目安 ~5:1)")
        if so < 3:
            print("⚠️ opus昇格が多い。REJECT基準(2回で昇格)を守れているか確認。")
    if fable:
        of = round(opus / fable, 1)
        print(f"opus:fable(deep-solver) = {of}:1  (稀であるほど健全。目標値は設けない)")
        if of < 4:
            print("🚨 deep-solverが常用されている。opus層が繰り返し失敗している原因、"
                  "またはclassifierフォールバックを確認(model-tiering.md 運用上の注意 #3)。")
        elif of < 10:
            print("⚠️ deep-solverの発火がやや多い。opus層の失敗傾向を点検。")
    elif sonnet or opus:
        print("opus:fable(deep-solver) = deep-solver発火なし（健全）")
else:
    print('(missing — 自己改善ループ未実施 or タスク未完了)')
