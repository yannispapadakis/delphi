#!/bin/bash

replace_nova_conf()
{
	which_one=$1 ## Can be one of openstack, gps, gno, actimanager
	cp /home/ypap/actimanager/actimanager/openstack_components/conf/nova.${which_one}.conf /etc/nova/nova.conf
	chown nova:nova /etc/nova/nova.conf
	/etc/init.d/nova-scheduler restart
}

run_perf()
{
	vm=$1
	vcpus=$2
	tool=$3
	echo $(date +"%T") "Running" $vm "(" $vcpus "vcpus) with" $tool
	output_file=${vm}_${vcpus}-${tool}.txt
	./isolation.py ${vm} ${vcpus} ${tool} &> ../results/${output_file}
}

run_attacker()
{
	vm=$1
	vcpus=$2

	for att in "l3" "memBw"; do
		echo $(date +"%T") "Running" $vm "(" $vcpus "vcpus) against" $att
		output_file=${vm}_${vcpus}-${att}.txt
		python attackers.py $vm $vcpus acticloud1 $att &> ../results/attackers/${output_file}
	done
}

spec_benchmarks="astar,bzip2,bwaves,cactusADM,calculix,dealII,gamess,gcc,GemsFDTD,gobmk,gromacs,h264ref,hmmer,lbm,leslie3d,libquantum,mcf,milc,namd,omnetpp,perlbench,povray,sjeng,soplex,sphinx3,tonto,xalancbmk,zeusmp"
parsec_benchmarks="blackscholes,bodytrack,canneal,dedup,facesim,ferret,fluidanimate,freqmine,streamcluster,swaptions,vips,x264"
benchmarks="img-dnn,masstree,moses,shore,silo,tailbench.sphinx"

tool=$1
vcpus=$2
replace_nova_conf "gno"
source /root/admin_openrc

openstack server start vm1-${vcpus}
sleep 60
output_file="internal-${tool}.txt"
python /home/ypap/actimanager/actimanager/Internal.py acticloud1 pps &> ../results/${output_file} &
internal_pid="$!"
echo "Spawned Internal on acticloud1 with PID: $internal_pid"

IFS=',' read -r -a benches <<< "$benchmarks"
for vm in ${benches[@]}; do
	run_perf $vm $vcpus $tool
	#run_attacker $vm $vcpus
done

kill -15 $internal_pid
openstack server stop vm1-${vcpus}
