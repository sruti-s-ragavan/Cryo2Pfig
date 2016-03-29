#!/bin/bash
python /Users/srutis90/Projects/VFT/Cryo2Pfig/PFIS/pfis3/scripts/runScript.py \
	-A \
	-e /Users/srutis90/Projects/VFT/Cryo2Pfig/PFIS/pfis3/src/python/pfis3.py \
    -d /Users/srutis90/Projects/VFT/DB-corrected/small \
	-s /Users/srutis90/Projects/VFT/Cryo2Pfig/PFIS/je.txt \
	-l "JS" \
	-t 1 \
	-p /Users/srutis90/Projects/VFT/Cryo2Pfig/jsparser/src \
	-o /Users/srutis90/Projects/VFT/Cryo2Pfig/PFIS/results \
	-x /Users/srutis90/Projects/VFT/Cryo2Pfig/PFIS/algorithm-config.xml \
	-c "combined-results.txt" \
	-m "multi-factors.txt" \
	-h "10" \
	-i "0" \
	-f "results.final" \
	-n "top-predictions"
