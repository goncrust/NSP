#!/bin/bash

timeoutInSeconds=1800

if [[ ! -f nsp-checker ]]; then
    echo "Before running this script you need to unzip the nsp-checker (compiled for your OS) in this directory."
    exit 0
fi

chmod +x proj1 project1.py nsp-checker

for f in public-tests/*.nsp
do
    fbase="${f%.*}"
    fbase=$(basename $fbase)
    outfile=public-tests/"$fbase.myout"
    checkfile=public-tests/"$fbase.check"
    echo "Executing on instance $f"
    time timeout $timeoutInSeconds"s" ./project1.py < "$f" > "$outfile"
    ./nsp-checker "$f" "$outfile" > "$checkfile"
    cat "$checkfile"
    echo
    echo
    echo
done

