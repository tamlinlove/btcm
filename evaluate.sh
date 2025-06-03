#!/bin/bash
python multi_explain.py -p1 default -p2 frustrated --max_depth 2 --max_follow_ups 4
python multi_explain.py -p1 default -p2 no_attention --max_depth 2 --max_follow_ups 4
python multi_explain.py -p1 default -p2 no_reactivity --max_depth 2 --max_follow_ups 4
python multi_explain.py -p1 default -p2 no_memory --max_depth 2 --max_follow_ups 4