#!/bin/bash
# Pilot: 2 tasks x 3 conditions x 3 reps, sonnet, 3 in parallel. Order interleaves conditions.
cd "$(dirname "$0")"
one() {
  set -- $1
  python3 run.py "$1" "$2" "$3" --model sonnet >> runs/_progress.log 2>&1 \
    && python3 judge.py "runs/$1_$2_r$3" >> runs/_progress.log 2>&1 \
    && python3 claims.py "runs/$1_$2_r$3" >> runs/_progress.log 2>&1
  echo "DONE $1 $2 $3" >> runs/_progress.log
}
export -f one
for rep in 1 2 3; do for task in A_invoice B_slugify; do for cond in P0 P1 H; do
  echo "$task $cond $rep"; done; done; done | xargs -P 3 -I{} bash -c 'one "{}"'
echo "ALL DONE" >> runs/_progress.log
