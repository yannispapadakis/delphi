#!/bin/bash

replace_nova_conf()
{
	which_one=$1 ## Can be one of openstack, gps, gno, actimanager
	cp ../actimanager/openstack_components/conf/nova.${which_one}.conf /etc/nova/nova.conf
	chown nova:nova /etc/nova/nova.conf
	/etc/init.d/nova-scheduler restart
}

run_pairs()
{
	vm_file=$1

	replace_nova_conf "gno"

	base_filename="$(echo $vm_file | cut -d'.' -f1)_oracle1"

	## Start ACTiManager.internal daemons
	internal_pids=""
	IFS=',' read -r -a node <<< "$2"
	for i in ${node[@]}; do
		echo "Spawn Internal on acticloud$i"
		output_file="${base_filename}.internal-acticloud$i.txt"
		python ../actimanager/Internal.py acticloud$i pps &> results/internal_outputs/${output_file} &
		internal_pids="${internal_pids} $!"
	done

	echo "Executing Pairs..."
	output_file="${base_filename}.txt"
	python n_pairs.py ${vm_file} $2 &> results/${output_file}

	sleep 30
	echo "killing ACTiManager.internal daemons with pids: $internal_pids"
	kill -9 $internal_pids
}

clear_openstack_vms()
{
	node=$1
	echo "Deleting all openstack VMs from acticloud$node"
	for i in `openstack server list --host acticloud${node} -f value -c ID`; do openstack server delete $i; done
	sleep 10
}

## On exit kill all background jobs
on_exit()
{
	echo -n "killing all background jobs ($(jobs -p | tr '\n' ' ')) before exiting..."
	kill $(jobs -p)
}
trap on_exit EXIT

nodes="3,4"
IFS=',' read -r -a nd <<< "$nodes"
for i in ${nd[@]}; do
	clear_openstack_vms $i
done

bench_file=$1

run_pairs ${bench_file} $nodes

for i in ${nd[@]}; do
	clear_openstack_vms $i
done

