#!/usr/bin/env bash

#set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 numDays numShiftsPerDay numNurses" >&2
  exit 1
fi

nDays="$1"
nShifts="$2"
nNurses="$3"

MIN=1

UNAV=0.15
MAXPCT=0.4
MAXCOST=5
BASE_SEED=0

D_MAX=10
D_STEP=2

S_MAX=6
S_STEP=1

N_MAX=30
N_STEP=5

I_MAX=5
I_STEP=1

# Ensure output directory exists
OUT_DIR="custom_tests"
mkdir -p "$OUT_DIR"

if [[ -n "$BASE_SEED" ]]; then
        seed="$BASE_SEED"
    else
        seed=$RANDOM
    fi


for (( nk = nNurses; nk < nNurses + N_MAX; nk += N_STEP )); do
    for (( d = nDays; d < nDays + D_MAX; d += D_STEP )); do
        for (( s = nShifts; s < nShifts + S_MAX; s += S_STEP )); do
            for (( i = 0; i < I_MAX; i += I_STEP )); do
                MAX="$s"

                mkdir -p "$OUT_DIR/${nk}_${d}_${s}/"
                outfile="$OUT_DIR/${nk}_${d}_${s}/${i}.nsp"

                ./generator "$d" "$s" "$nk" \
                    "$MIN" "$MAX" "$UNAV"   \
                    "$MAXPCT" "$MAXCOST"    \
                    "$seed" > "$outfile"

                echo "Generated D=$d, S=$s, N=$nk  -> $outfile  (seed=$seed)"

                (( seed++ ))
            done
            (( seed -= NUM_INSTANCES))
        done
    done
done


echo "Generated $NUM_INSTANCES instances in '$OUT_DIR/'."
