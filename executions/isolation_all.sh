#!/bin/bash

run_perf()
{
	vm=$1
	vcpus=$2
	node=$3
	tool=$4
	echo $(date +"%T") "Running" $vm "(" $vcpus "vcpus) with" $tool
	output_file=${vm}_${vcpus}-${tool}.txt
	python isolation.py ${vm} ${vcpus} acticloud${node} ${tool} &> ../results/${output_file}
}

run_attacker()
{
	vm=$1
	vcpus=$2
	node=$3

	for att in "l3" "memBw"; do
		echo $(date +"%T") "Running" $vm "(" $vcpus "vcpus) against" $att "on node" $node
		output_file=${vm}_${vcpus}-${att}.txt
		python attackers.py $vm $vcpus acticloud${node} $att &> ../results/attackers/${output_file}
	done
}

node="1"
tool="pqos"

benchmarks="astar,bzip2,bwaves,cactusADM,calculix,dealII,gamess,gcc,GemsFDTD,gobmk,gromacs,h264ref,hmmer,lbm,leslie3d,libquantum,mcf,milc,namd,omnetpp,perlbench,povray,sjeng,soplex,sphinx3,tonto,xalancbmk,zeusmp"
benchmarks="blackscholes,bodytrack,canneal,dedup,facesim,ferret,fluidanimate,freqmine,streamcluster,swaptions,vips,x264"
IFS=',' read -r -a benches <<< "$benchmarks"

for vm in ${benches[@]}; do
	vcpus_str="1,2,4,8"
	IFS=',' read -r -a vcpus <<< "$vcpus_str"
	for v in ${vcpus[@]}; do
		run_perf $vm $v $node $tool
		#run_attacker $vm $vcpus $node
	done
done
