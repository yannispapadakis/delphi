#!/bin/bash

replace_nova_conf()
{
	which_one=$1 ## Can be one of openstack, gps, gno, actimanager
	cp ../actimanager/openstack_components/conf/nova.${which_one}.conf /etc/nova/nova.conf
	chown nova:nova /etc/nova/nova.conf
	/etc/init.d/nova-scheduler restart
}

trap on_exit EXIT

spec_benchmarks="astar,bzip2,bwaves,cactusADM,calculix,dealII,gamess,gcc,GemsFDTD,gobmk,gromacs,h264ref,hmmer,lbm,leslie3d,libquantum,mcf,milc,namd,omnetpp,perlbench,povray,sjeng,soplex,sphinx3,tonto,xalancbmk,zeusmp"
parsec_benchmarks="blackscholes,bodytrack,canneal,dedup,facesim,ferret,fluidanimate,freqmine,streamcluster,swaptions,vips,x264"

replace_nova_conf "gno"
spec_vcpus=1
parsec_vcpus=1
output_file="internal-spec.${spec_vcpus}_parsec.${parsec_vcpus}.txt"
python /home/ypap/actimanager/actimanager/Internal.py acticloud1 pps &> ../results/${output_file} &
internal_pid="$!"
echo "Spawned Internal on acticloud1 with PID: $internal_pid"

IFS=',' read -r -a specs <<< "$spec_benchmarks"
for spec in ${specs[@]}; do
	IFS=',' read -r -a parsecs <<< "$parsec_benchmarks"
	for parsec in ${parsecs[@]}; do
		output_file="${spec}_${spec_vcpus}-${parsec}_${parsec_vcpus}.txt"
		python heatmap_run.py $spec $spec_vcpus $parsec $parsec_vcpus &> ../results/${output_file}
	done
done

kill -9 $internal_pid
echo "Finished, stopped Internal"
