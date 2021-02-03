#!/bin/bash
for i in $(seq 1 $1); do
    python build_dataset.py Lang $i $2/Lang-faults-$i.json
done

for i in $(seq 1 $1); do
    python build_dataset.py Chart $i $2/Chart-faults-$i.json
done

for i in $(seq 1 $1); do
    python build_dataset.py Time $i $2/Time-faults-$i.json
done

for i in $(seq 1 $1); do
    python build_dataset.py Math $i $2/Math-faults-$i.json
done

for i in $(seq 1 $1); do
    python build_dataset.py Closure $i $2/Closure-faults-$i.json
done
