#!/bin/bash

replace_nova_conf()
{
	which_one=$1 ## Can be one of openstack, gps, gno, actimanager
	cp /home/ypap/actimanager/actimanager/openstack_components/conf/nova.${which_one}.conf /etc/nova/nova.conf
	chown nova:nova /etc/nova/nova.conf
	/etc/init.d/nova-scheduler restart
}

parsec_benchmarks="blackscholes,bodytrack,canneal,dedup,facesim,ferret,fluidanimate,freqmine,streamcluster,swaptions,vips,x264"
spec_benchmarks="astar,bzip2,bwaves,cactusADM,calculix,dealII,gamess,gcc,GemsFDTD,gobmk,gromacs,h264ref,hmmer,lbm,leslie3d,libquantum,mcf,milc,namd,omnetpp,perlbench,povray,sjeng,soplex,sphinx3,tonto,xalancbmk,zeusmp"

replace_nova_conf "gno"
parsec_vcpus=$1
spec_vcpus=$2
source /root/admin_openrc
sleep 1
openstack server start vm1-${parsec_vcpus}_core vm2-${spec_vcpus}_core
sleep 60

output_file="internal-spec.${spec_vcpus}_parsec.${parsec_vcpus}.txt"
python /home/ypap/actimanager/actimanager/Internal.py acticloud1 pps &> ../results/${output_file} &
internal_pid="$!"
echo "Spawned Internal on acticloud1 with PID: $internal_pid"

IFS=',' read -r -a parsecs <<< "$parsec_benchmarks"
for parsec in ${parsecs[@]}; do
	IFS=',' read -r -a specs <<< "$spec_benchmarks"
	for spec in ${specs[@]}; do
		echo $(date +"%T") "Running:" $parsec "(" $parsec_vcpus ")" "vs" $spec "(" $spec_vcpus ")"
		output_file="${parsec}_${parsec_vcpus}-${spec}_${spec_vcpus}.txt"
		python heatmap_run.py $parsec $parsec_vcpus $spec $spec_vcpus &> ../results/coexecutions/${parsec}/${parsec_vcpus}vs${spec_vcpus}/${output_file}
	done
done

openstack server stop vm1-${parsec_vcpus}_core vm2-${spec_vcpus}_core
echo "Parsec (" $parsec_vcpus "vcpus) VS Spec (" $spec_vcpus "vcpus) finished"
