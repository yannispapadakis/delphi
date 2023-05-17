#!/usr/bin/python
from heatmap_run import *

def multiple_run(benchmarks, port):
	hosts = dict()
	pids = dict()
	vms_vcpus = {2: 1, 4: 1}
	tails = 0
	for (i, benchmark) in enumerate(benchmarks):
		vcpus = int(benchmark['nr_vcpus'])
		host = 'vm' + str(vms_vcpus[vcpus]) + '-' + str(vcpus)
		vms_vcpus[vcpus] += 1
		hosts[i] = host
		commands = get_vm_commands(i, benchmark, port, vm_ips[host])
		verify_empty_host(host)
		if "tailbench" in benchmark['bench'][0]:
			client_vm = 'client-' + str(tails % 2 + 1)
			tails += 1
			hosts[i] = (host, client_vm)
			server, client = commands.split(sc_split)
			ssh_server = "ssh " + host + " \'" + server + "\' &"
			ssh_client = "ssh " + client_vm + " \'" + client + "\' &"
			os.system(ssh_server)
			os.system(ssh_client)
			pids[client_vm] = (i, ssh_command_pid(client_vm))
		else:
			ssh_command = "ssh " + host + " \'" + commands + "\' &"
			os.system(ssh_command)
			pids[host] = (i, ssh_command_pid(host))

	completed = []
	finished = []
	while len(completed) < len(benchmarks):
		for f in finished:
			host = hosts[f]
			if type(host) == tuple: (host, client_vm) = host
			extra_command = get_vm_commands(f, benchmarks[f], port, vm_ips[host], True)
			if "tailbench" in benchmarks[f]['bench'][0]:
				extra_command, client = extra_command.split(sc_split)
				ssh_client = "ssh " + client_vm + " \'" + client + "\' &"
			ssh_command = "ssh " + host + " \'" + extra_command + "\' &"
			os.system(ssh_command)
			if "tailbench" in benchmarks[f]['bench'][0]:
				os.system(ssh_client)
				pids[client_vm] = (f, ssh_command_pid(client_vm))
			else:
				pids[host] = (f, ssh_command_pid(host))
		finished = find_finished_benchmark(pids)
		completed = list(set(completed + finished))
	for c in completed:
		print "Killing:", c, benchmarks[c]['bench'][0]
		if "spec" in benchmarks[c]['bench'][0]:
			kill_spec(hosts[c])
		elif "parsec" in benchmarks[c]['bench'][0]:
			kill_parsec(hosts[c])
		elif "tailbench" in benchmarks[c]['bench'][0]:
			kill_tailbench('client-1')
			kill_tailbench('client-2')
	logger.info("All VMs finished")				

def run_m_benchmarks_1vcpu_support_incomplete(benchmarks, port):
	vcpus_per_host = dict((x, 0) for x in filter(lambda x: x.startswith('vm'), list(vm_ips.keys())))
	tails = len(filter(lambda x: 'tailbench' in x['bench'][0], benchmarks))
	for (i, benchmark) in enumerate(benchmarks):
		host = list(filter(lambda x: vcpus_per_host[x] + vcpus <= int(x[-1]), vcpus_per_host))[0]
		vcpus_per_host[host] += int(vcpus)

if __name__ == "__main__":
	PORT = 8081
	vm_messages_monitor.spawn_monitor_thread()
	signal.signal(signal.SIGTERM, signal_handler)
	signal.signal(signal.SIGINT, signal_handler)

	bench_input = [(sys.argv[x], int(sys.argv[x+1])) for x in range(1, len(sys.argv), 2)]
	multiple_run(generate_vms_list(bench_input), PORT)
	vm_messages_monitor.stop_monitor_thread()
