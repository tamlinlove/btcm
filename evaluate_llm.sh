#!/bin/bash

profiles=("frustrated" "no_attention" "no_reactivity" "no_memory")

for profile in "${profiles[@]}"; do
    python llm_eval.py -p1 default -p2 "$profile" -m deepseek-r1:32b
done