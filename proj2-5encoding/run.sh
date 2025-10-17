#!/bin/bash

VENV_PYTHON="$HOME/Documents/dev/venvs/nsp/bin/python"

timeoutInSeconds=600

if [[ ! -f nsp-checker ]]; then
    echo "Before running this script you need to unzip the nsp-checker (compiled for your OS) in this directory."
    exit 0
fi

chmod +x project2.py nsp-checker

for f in public-tests/*.nsp
do
    fbase="${f%.*}"
    fbase=$(basename $fbase)
    outfile=public-tests/"$fbase.myout"
    checkfile=public-tests/"$fbase.check"
    echo "Executing on instance $f"
    time timeout $timeoutInSeconds"s" "$VENV_PYTHON" ./project2.py < "$f" > "$outfile"
    ./nsp-checker "$f" "$outfile" > "$checkfile"
    cat "$checkfile"
    echo
    echo
    echo
done

