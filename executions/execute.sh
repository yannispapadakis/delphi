#!/bin/bash

replace_nova_conf()
{
	which_one=$1 ## Can be one of openstack, gps, gno, actimanager
	cp /home/ypap/actimanager/actimanager/openstack_components/conf/nova.${which_one}.conf /etc/nova/nova.conf
	chown nova:nova /etc/nova/nova.conf
	/etc/init.d/nova-scheduler restart
}

run_isolation()
{
	benchmarks=$1
	vcpus=$2
	tool=$3

	openstack server start vm1-${vcpus}
	sleep 60

	IFS=',' read -r -a benches <<< "$benchmarks"
	for vm in ${benches[@]}; do
		echo $(date +"%F %T") ":" $vm "(" $vcpus ")" $tool
		output_file=${vm}_${vcpus}-${tool}.txt
		./isolation.py ${vm} ${vcpus} ${tool} &> ../results/${output_file}
	done
	openstack server stop vm1-${vcpus}
}

run_coexecution()
{
	benchmarks1=$1
	vcpus1=$2
	benchmarks2=$3
	vcpus2=$4

	openstack server start vm1-${vcpus1} vm2-${vcpus2}
	sleep 60

	IFS=',' read -r -a benches1 <<< "$benchmarks1"
	for i in ${!benches1[@]}; do
		IFS=',' read -r -a benches2 <<< "$benchmarks2"
		for j in ${!benches2[@]}; do
			if [[ ("${benches1[$i]}" == "shore" && "$vcpus1" == "1") || ("${benches1[$i]}" == "masstree" && "$vcpus1" == "8") ]]; then
				continue
			fi
			#if [ $j -ge $i ]; then
			echo $(date +"%F %T") ":" "${benches1[$i]}" "(" $vcpus1 ")" "vs" "${benches2[$j]}" "(" $vcpus2 ")"
			output_file="${benches1[$i]}_${vcpus1}-${benches2[$j]}_${vcpus2}.txt"
			./heatmap_run.py ${benches1[$i]} $vcpus ${benches2[$j]} $vcpus2 &> ../results/${output_file}
			#fi
		done
		./cleaner.py ${benches1[$i]}
	done
	rm ../results/internal.txt
	openstack server stop vm1-${vcpus1} vm2-${vcpus2}
}

specs="astar,bzip2,bwaves,cactusADM,calculix,dealII,gamess,gcc,GemsFDTD,gobmk,gromacs,h264ref,hmmer,lbm,leslie3d,libquantum,mcf,milc,namd,omnetpp,perlbench,povray,sjeng,soplex,sphinx3,tonto,xalancbmk,zeusmp"
parsecs="blackscholes,bodytrack,canneal,dedup,facesim,ferret,fluidanimate,freqmine,streamcluster,swaptions,vips,x264"
tails="img-dnn,masstree,moses,shore,silo,tailbench.sphinx"

benchmarks()
{
	bench_str=$1
	if [ "$bench_str" = "spec" ]; then
		benches=$specs
	elif [ "$bench_str" = "parsec" ]; then
		benches=$parsecs
	elif [ "$bench_str" = "tail" ]; then
		benches=$tails
	fi
}

if [ $# -lt 3 ]; then
	echo "|  ISOLATION  | ./execute.sh <benchmarks>  <vcpus>  <tool>                 |"
	echo "| COEXECUTION | ./execute.sh <benchmarks1> <vcpus1> <benchmarks2> <vcpus2> |"
fi

replace_nova_conf "gno"
source /root/admin_openrc

python /home/ypap/actimanager/actimanager/Internal.py acticloud1 pps &> ../results/internal.txt &
internal_pid="$!"

benchmarks $1
vcpus=$2
if [ $# -eq 3 ]; then
	run_isolation $benches $vcpus $3
elif [ $# -eq 4 ]; then
	benches1=$benches
	benchmarks $3
	vcpus2=$4
	run_coexecution $benches1 $vcpus $benches $vcpus2
fi

kill -15 $internal_pid
