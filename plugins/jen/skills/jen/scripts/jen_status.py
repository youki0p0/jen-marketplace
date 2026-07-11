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

# Ratio Guard (v3.5): sonnet:opus:fable の実測比率を .jen/routing-stats.json から集計する。
# 目標は約20:4:1（references/model-tiering.md「目標分布」参照）。強制はしない自己点検用。
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
    print(f"sonnet={sonnet} opus={opus} fable={fable} haiku={haiku}")

    if opus:
        so = round(sonnet / opus, 1)
        print(f"sonnet:opus = {so}:1  (目標 ~5:1)")
        if so < 3:
            print("⚠️ opus昇格が多い。REJECT基準(2回で昇格)を守れているか確認。")
    if fable:
        of = round(opus / fable, 1)
        print(f"opus:fable = {of}:1  (目標 ~4:1)")
        if of < 2:
            print("⚠️ fable(deep-solver)発火が多い。opus層の失敗原因、"
                  "またはclassifierフォールバックを確認(model-tiering.md 運用上の注意 #3)。")
else:
    print('(missing — 自己改善ループ未実施 or タスク未完了)')
