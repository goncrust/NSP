#!/bin/bash

set -eo pipefail

if [[ $# -eq 3 ]]; then
    echo "Generating custom tests with: D=$1 S=$2 N=$3"
    ./../proj_generator/generate_custom_tests.sh "$1" "$2" "$3"
elif [[ $# -ne 0 ]]; then
    echo "Usage: $0 [numDays numShiftsPerDay numNurses]" >&2
    exit 1
fi

timeoutInSeconds=600

if [[ ! -x ./nsp-checker ]]; then
    echo "Before running this script you need to unzip the nsp-checker (compiled for your OS) in this directory."
    exit 1
fi
chmod +x project2.py nsp-checker

ROOT="../proj_generator/custom_tests"
CSV_OUT="../data5.csv"

echo "dir,x_values,files,ok,failed,timeouts,avg_seconds" > "$CSV_OUT"

for dir in "$ROOT"/*_*_*; do
    [[ -d "$dir" ]] || continue

    base="$(basename "$dir")"
    # Safe parse without touching IFS
    nurses=${base%%_*}
    rest=${base#*_}
    days=${rest%%_*}
    shifts=${rest##*_}


    echo "Processing $base."

    # Collect *.nsp files inside this dir
    files=( "$dir"/*.nsp )
    if ((${#files[@]} == 0)); then
        echo "   (no .nsp files in $dir)"
        echo "$base,$days,$shifts,$nurses,0,0,0,0,0.000" >> "$CSV_OUT"
        continue
    fi

    ok=0
    failed=0
    timeouts=0
    sum=0.0

    for f in "${files[@]}"; do
        stem="${f##*/}"; stem="${stem%.*}"
        outfile="$dir/$stem.myout"
        checkfile="$dir/$stem.check"

        echo "   - Running $f"

        # Measure runtime with /usr/bin/time; capture status
        # (time prints to stderr; we capture it in rt)
        rt="$(
            { /usr/bin/time -f '%e' timeout "${timeoutInSeconds}s" ./project2.py < "$f" > "$outfile"; } 2>&1 >/dev/null
        )" || status=$? || true

        # Determine status (0=ok, 124=timeout from GNU timeout, otherwise failed)
        status=${status:-0}
        if [[ $status -eq 0 ]]; then
            ok=$((ok+1))
            # add runtime (rt) to sum as float
            sum=$(awk -v a="$sum" -v b="$rt" 'BEGIN{printf "%.6f", a + b}')
            ./nsp-checker "$f" "$outfile" > "$checkfile" || true
        elif [[ $status -eq 124 ]]; then
            timeouts=$((timeouts+1))
            echo " Timeout after ${timeoutInSeconds}s"
            rm -f "$outfile"
        else
            failed=$((failed+1))
            echo "Failed with status $status"
            rm -f "$outfile"
        fi

        unset status
    done

    if (( ok > 0 )); then
        avg=$(awk -v s="$sum" -v c="$ok" 'BEGIN{printf "%.6f", s / c}')
    else
        avg="0.000000"
    fi

    total=$((days * shifts * nurses))
    echo "$base, $total,${#files[@]},$ok,$failed,$timeouts,$avg" >> "$CSV_OUT"

    echo "dir=$base  files=${#files[@]}  ok=$ok  failed=$failed  timeouts=$timeouts  avg=${avg}s"
done

echo
echo "CSV written to: $CSV_OUT"