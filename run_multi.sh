#!/bin/bash

profiles=("default" "frustrated" "no_attention" "no_reactivity" "no_memory")
num_runs=50

python multi_run.py -p "${profiles[@]}" -n "$num_runs"