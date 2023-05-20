#!/bin/bash

replace_nova_conf()
{
	which_one=$1 ## Can be one of openstack, gps, gno, actimanager
	cp /home/ypap/actimanager/actimanager/openstack_components/conf/nova.${which_one}.conf /etc/nova/nova.conf
	chown nova:nova /etc/nova/nova.conf
	/etc/init.d/nova-scheduler restart
}

coexecution3()
{
	echo $(date +"%F %T") ":" "$1" "(" "$2" ")" "$3" "(" "$4" ")" "$5" "(" "$6" ")"
	output_file="$1_$2-$3_$4-$5_$6.txt"
	/home/ypap/delphi/executions/multiple_run.py $1 $2 $3 $4 $5 $6 &> /home/ypap/delphi/results/3ads/${output_file}
}

coexecution4()
{
	echo $(date +"%F %T") ":" "$1" "(" "$2" ")" "$3" "(" "$4" ")" "$5" "(" "$6" ")" "$7" "(" "$8" ")"
	output_file="$1_$2-$3_$4-$5_$6-$7_$8.txt"
	/home/ypap/delphi/executions/multiple_run.py $1 $2 $3 $4 $5 $6 $7 $8 &> /home/ypap/delphi/results/4ads/${output_file}
}

coexecution5()
{
	echo $(date +"%F %T") ":" "$1" "(" "$2" ")" "$3" "(" "$4" ")" "$5" "(" "$6" ")" "$7" "(" "$8" ")" "$9" "(" "${10}" ")"
	output_file="$1_$2-$3_$4-$5_$6-$7_$8-$9_${10}.txt"
	/home/ypap/delphi/executions/multiple_run.py $1 $2 $3 $4 $5 $6 $7 $8 $9 ${10} &> /home/ypap/delphi/results/5ads/${output_file}
}


replace_nova_conf "gno"
source /root/admin_openrc

python /home/ypap/actimanager/actimanager/Internal.py acticloud1 pps &> /home/ypap/delphi/results/internal.txt &
internal_pid="$!"
sleep 60

if [ $# -eq 6 ]; then
	if [[ $2 -eq 2 && $4 -eq 2 && $6 -eq 2 ]]; then
		openstack server start vm1-2 vm2-2 vm3-2
	elif [[ $2 -eq 4 && $4 -eq 2 && $6 -eq 2 ]]; then
		openstack server start vm1-4 vm1-2 vm2-2
	elif [[ $2 -eq 4 && $4 -eq 4 && $6 -eq 2 ]]; then
		openstack server start vm1-4 vm2-4 vm1-2
	elif [[ $2 -eq 2 && $4 -eq 4 && $6 -eq 2 ]]; then
		openstack server start vm1-4 vm2-4 vm1-2
	elif [[ $2 -eq 2 && $4 -eq 2 && $6 -eq 4 ]]; then
		openstack server start vm1-2 vm2-2 vm1-4
	elif [[ $2 -eq 2 && $4 -eq 4 && $6 -eq 4 ]]; then
		openstack server start vm1-4 vm2-4 vm1-2
	elif [[ $2 -eq 4 && $4 -eq 2 && $6 -eq 4 ]]; then
		openstack server start vm1-4 vm2-4 vm1-2
	fi
	sleep 60
	coexecution3 $1 $2 $3 $4 $5 $6
	if [[ $2 -eq 2 && $4 -eq 2 && $6 -eq 2 ]]; then
		openstack server stop vm1-2 vm2-2 vm3-2
	elif [[ $2 -eq 4 && $4 -eq 2 && $6 -eq 2 ]]; then
		openstack server stop vm1-4 vm1-2 vm2-2
	elif [[ $2 -eq 4 && $4 -eq 4 && $6 -eq 2 ]]; then
		openstack server stop vm1-4 vm2-4 vm1-2
	elif [[ $2 -eq 2 && $4 -eq 2 && $6 -eq 4 ]]; then
		openstack server stop vm1-2 vm2-2 vm1-4
	elif [[ $2 -eq 2 && $4 -eq 4 && $6 -eq 4 ]]; then
		openstack server stop vm1-4 vm2-4 vm1-2
	elif [[ $2 -eq 4 && $4 -eq 2 && $6 -eq 4 ]]; then
		openstack server stop vm1-4 vm2-4 vm1-2
	fi
	/home/ypap/delphi/executions/cleaner.py 3
elif [ $# -eq 8 ]; then
	if [[ $2 -eq 2 && $4 -eq 2 && $6 -eq 2 && $8 -eq 2 ]]; then
		openstack server start vm1-2 vm2-2 vm3-2 vm4-2
	elif [[ $2 -eq 4 && $4 -eq 2 && $6 -eq 2 && $8 -eq 2 ]]; then
		openstack server start vm1-4 vm1-2 vm2-2 vm3-2
	fi
	sleep 60
	coexecution4 $1 $2 $3 $4 $5 $6 $7 $8
	if [[ $2 -eq 2 && $4 -eq 2 && $6 -eq 2 && $8 -eq 2 ]]; then
		openstack server stop vm1-2 vm2-2 vm3-2 vm4-2
	elif [[ $2 -eq 4 && $4 -eq 2 && $6 -eq 2 && $8 -eq 2 ]]; then
		openstack server stop vm1-4 vm1-2 vm2-2 vm3-2
	fi
	/home/ypap/delphi/executions/cleaner.py 4
elif [ $# -eq 10 ]; then
	openstack server start vm1-2 vm2-2 vm3-2 vm4-2 vm5-2
	sleep 60
	coexecution5 $1 $2 $3 $4 $5 $6 $7 $8 $9 ${10}
	openstack server stop vm1-2 vm2-2 vm3-2 vm4-2 vm5-2
	/home/ypap/delphi/executions/cleaner.py 5
fi

sleep 60
kill -15 $internal_pid
rm /home/ypap/delphi/results/internal.txt

#(0, 0): vips, sphinx3, streamcluster, facesim, x264, bodytrack, swaptions, freqmine, dedup, blackscholes, ferret
#(0, 1): GemsFDTD, leslie3d, lbm, libquantum
#(1, 0): masstree, gcc, tailbench.sphinx, xalancbmk, perlbench, cactusADM, silo, img-dnn, astar
#(1, 1): soplex, mcf, milc
#r3="vips_lbm_perlbench,ferret_lbm_mcf,dedup_astar_milc,leslie3d_perlbench_soplex"
#IFS=',' read -r -a r0 <<< "$r3"
#for run in ${r0[@]}; do
#	IFS='_' read -r -a benches <<< "$run"
#	coexecution3 ${benches[0]} ${benches[1]} ${benches[2]}
##	coexecution4 ${benches[0]} ${benches[1]} ${benches[2]} ${benches[3]}
##	coexecution5 ${benches[0]} ${benches[1]} ${benches[2]} ${benches[3]} ${benches[4]}
#done
