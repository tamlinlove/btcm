#!/bin/bash

profiles=("frustrated" "no_attention" "no_reactivity" "no_memory")

for profile in "${profiles[@]}"; do
    python llm_eval.py -p1 default -p2 "$profile" -m phi4
    # python llm_eval.py -p1 default -p2 "$profile" -m deepseek-r1:32b
    # python llm_eval.py -p1 default -p2 "$profile" -m deepseek-r1:32b --use_simple_prompt
    # python llm_eval.py -p1 default -p2 "$profile" -m phi4 --use_simple_prompt
done