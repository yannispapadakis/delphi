#!/bin/bash

replace_nova_conf()
{
	which_one=$1 ## Can be one of openstack, gps, gno, actimanager
	cp /home/ypap/actimanager/actimanager/openstack_components/conf/nova.${which_one}.conf /etc/nova/nova.conf
	chown nova:nova /etc/nova/nova.conf
	/etc/init.d/nova-scheduler restart
}

spec_benchmarks="astar,bzip2,bwaves,cactusADM,calculix,dealII,gamess,gcc,GemsFDTD,gobmk,gromacs,h264ref,hmmer,lbm,leslie3d,libquantum,mcf,milc,namd,omnetpp,perlbench,povray,sjeng,soplex,sphinx3,tonto,xalancbmk,zeusmp"
parsec_benchmarks="blackscholes,bodytrack,canneal,dedup,facesim,ferret,fluidanimate,freqmine,streamcluster,swaptions,vips,x264"

replace_nova_conf "gno"
spec_vcpus=$2
parsec_vcpus=$1
source /root/admin_openrc
sleep 1
openstack server start vm1-${parsec_vcpus}_core vm2-${spec_vcpus}_core
sleep 60

output_file="internal-spec.${spec_vcpus}_parsec.${parsec_vcpus}.txt"
python /home/ypap/actimanager/actimanager/Internal.py acticloud1 pps &> ../results/${output_file} &
internal_pid="$!"
echo "Spawned Internal on acticloud1 with PID: $internal_pid"

IFS=',' read -r -a specs <<< "$spec_benchmarks"
for spec in ${specs[@]}; do
	IFS=',' read -r -a parsecs <<< "$parsec_benchmarks"
	for parsec in ${parsecs[@]}; do
		echo "Running:" $spec "(" $spec_vcpus ")" "vs" $parsec "(" $parsec_vcpus ")"
		output_file="${parsec}_${parsec_vcpus}-${spec}_${spec_vcpus}.txt"
		python heatmap_run.py $parsec $parsec_vcpus $spec $spec_vcpus &> ../results/coexecutions/${parsec}/${parsec_vcpus}vs${spec_vcpus}/${output_file}
	done
done

kill -9 $internal_pid
echo "Finished, stopped Internal"

openstack server stop vm1-${parsec_vcpus}_core vm2-${spec_vcpus}_core
sleep 30
