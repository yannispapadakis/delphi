#!/bin/bash

run_perf()
{
	vm=$1
	vcpus=$2
	node=$3
	tool=$4
	echo $(date +"%T") "Running" $vm "(" $vcpus "vcpus) with" $tool "on node" $node
	output_file=${vm}_${vcpus}-${tool}.txt
	python perf.py ${vm} ${vcpus} acticloud${node} ${tool} &> results/outputs/${output_file}
}

run_attacker()
{
	vm=$1
	vcpus=$2
	node=$3

	for att in "l3" "memBw"; do
		echo $(date +"%T") "Running" $vm "(" $vcpus "vcpus) against" $att "on node" $node
		output_file=${vm}_${vcpus}-${att}.txt
		python attackers.py $vm $vcpus acticloud${node} $att &> results/attackers/${output_file}
	done
}

benchmarks="astar,bzip2,bwaves,cactusADM,calculix,dealII,gamess,gcc,GemsFDTD,gobmk,gromacs,h264ref,hmmer,lbm,leslie3d,libquantum,mcf,milc,namd,omnetpp,perlbench,povray,sjeng,soplex,sphinx3,tonto,xalancbmk,zeusmp"
IFS=',' read -r -a benches <<< "$benchmarks"

vcpus_str="1,2,4,8"
IFS=',' read -r -a vcpus <<< "$vcpus_str"

node=$1
tool="perf"

for vm in ${benches[@]}; do
	for vcpus in ${vcpus[@]}; do
		run_perf $vm $vcpus $node $tool
		#run_attacker $vm $vcpus $node
	done
done
