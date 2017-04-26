#!/bin/bash

repo_root=$(pwd)
db_folder=$1

python "$repo_root/PFIS/pfis3/scripts/runScript.py" \
	-A \
	-e "$repo_root/PFIS/pfis3/src/python/pfis3.py" \
    -d "$db_folder" \
	-s "$repo_root/PFIS/je.txt" \
	-l "JS" \
	-t 1 \
	-p "$repo_root/jsparser/src" \
	-o "$repo_root/PFIS/results" \
	-x "$repo_root/configs/algorithm-config-variantNavPath.xml" \
	-c "combined-results.txt" \
	-m "multi-factors.txt" \
	-h "10" \
	-i "0" \
	-f "results.final" \
	-n "top-predictions" \
	-a "all-hitrates.txt"