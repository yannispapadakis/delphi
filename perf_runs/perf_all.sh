#!/bin/bash

node=$1
tool="perf"

for vm in "astar" "bzip2" "bwaves" "cactusADM" "gcc" "gromacs" "h264ref" "hmmer" "lbm" "leslie3d" "libquantum" "mcf" "namd" "omnetpp" "perlbench" "povray" "sjeng" "soplex" "xalancbmk" "zeusmp" "calculix" "dealII" "gamess" "GemsFDTD" "gobmk" "milc" "sphinx3" "tonto"; do
	for vcpus in "1" "2" "4" "8"; do
		echo $(date +"%T") "Running" $vm "with" $vcpus "vcpus..."
		output_file=${vm}_${vcpus}.txt
		python perf.py ${vm} ${vcpus} acticloud${node} ${tool} &> results/outputs/${output_file}
	done
done
