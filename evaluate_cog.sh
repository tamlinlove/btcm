#!/bin/bash

profiles=("frustrated" "no_attention" "no_reactivity" "no_memory")

for profile in "${profiles[@]}"; do
    python multi_explain.py -p1 default -p2 "$profile" --max_follow_ups 3 --max_depth 2
done