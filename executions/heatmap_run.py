#!/usr/bin/python
import sys
sys.path.append("../core/")
from benchmarks import *

def generate_vms_list(bench_input):
	benchmarks = list()
	for (bench_name, vcpus) in bench_input:
		bench = [x for x in benches_vcpus.items() if bench_name in x[0]]
		if len(bench) != 1:
			logger.error("Error in benchmark name: %s", bench_name)
			signal_handler(0, 0)
		benchmarks.append((bench[0], vcpus))

	runtimes = [bench[0][1]['runtime_isolation'][bench[1]] for bench in benchmarks]
	times_to_run = map(lambda x: int(2 * max(runtimes) / x), runtimes)
	return [{'nr_vcpus': vcpus, 'bench': benchmark, 'times_to_run': times_to_run[i]} for (i, (benchmark, vcpus)) in enumerate(benchmarks)]

def hostnames_to_ip():
	f = open("/root/.ssh/config")
	ips = dict()
	line = f.readline()
	while line:
		tokens = line.split()
		if "Host" in tokens: host = tokens[1]
		if "HostName" in tokens: ips[host] = tokens[1][-2:]
		line = f.readline()
	f.close()
	return ips

vm_ips = hostnames_to_ip()
sc_split = "|sc|"

def get_vm_commands(seq_num, vm_chars, port, ip, fill_in = False):
	vcpus = vm_chars['nr_vcpus']
	bench = vm_chars['bench']
	times_to_run = vm_chars['times_to_run']

	bench_name = bench[0]
	vm_name = bench_name.replace('.','-') if "parsec" in bench_name else bench_name
	vm_name = '-'.join(["acticloud1", "gold", vm_name, str(times_to_run) + "_times", "to_completion"])
	udata = ""

	if fill_in:
		if "spec-" in bench_name:
			spec_bench = bench_name.split('-')[1]
			udata += spec_extra % {"bench": spec_bench, "vcpus": vcpus}
		elif "parsec" in bench_name:
			udata += parsec_extra % {"bench": bench_name, "vcpus": vcpus}
		elif "tailbench" in bench_name:
			udata += tailbench_server % {"times_to_run": 1, "bench": bench_name.split('.')[1]}
			udata += sc_split
			udata += tailbench_client_extra % {"seq_num": seq_num, "vcpus": vcpus, "ip": ip,
											   "times_to_run": times_to_run, "bench": bench_name.split('.')[1], "port": port}
		elif "iperf" in bench_name:
			udata += iperf_server % {"times_to_run": 1, 'seq_num': 0, 'port': port}
			udata += sc_split
			udata += iperf_client % {"times_to_run": 1, "ip": ip}
	else:
		logger.info("Spawned new VM with seq_num: %d and name: %s", seq_num, vm_name)
		udata = vm_header % {"seq_num": seq_num, "port": port}
		if "spec-" in bench_name:
			#if "calculix" in bench_name: udata += vm_calculix
			spec_bench = bench_name.split('-')[1]
			udata += vm_spec % {"seq_num": seq_num, "vcpus": vcpus,
								"times_to_run": times_to_run, "bench": spec_bench, "port": port}
		elif "parsec" in bench_name:
			udata += vm_parsec % {"seq_num": seq_num, "vcpus": vcpus,
								  "times_to_run": times_to_run, "bench": bench_name, "port": port}
		elif "tailbench" in bench_name:
			udata += tailbench_server % {"times_to_run": times_to_run, "bench": bench_name.split('.')[1]}
			udata += vm_footer % {"seq_num": seq_num, "port": port}
			udata += sc_split
			suuid = subprocess.check_output("ssh root@10.0.100." + ip + " 'echo $(basename $(readlink -f /var/lib/cloud/instance))'", shell = True)[:-1]
			udata += client_header % {"suuid": suuid, "seq_num": seq_num, "port": port}
			udata += tailbench_client % {"seq_num": seq_num, "vcpus": vcpus, "ip": ip,
										 "times_to_run": times_to_run, "bench": bench_name.split('.')[1], "port": port}
		elif "iperf" in bench_name:
			udata += iperf_server % {"times_to_run": times_to_run, 'seq_num': 0, 'port': port}
			udata += vm_footer % {'port': port, "seq_num": 0}
			udata += sc_split
			suuid = subprocess.check_output("ssh root@10.0.100." + ip + " 'echo $(basename $(readlink -f /var/lib/cloud/instance))'", shell = True)[:-1]
			udata += client_header % {"suuid": suuid, "port": port, "seq_num": 0}
			udata += iperf_client % {"times_to_run": times_to_run, "ip": ip}
		udata += vm_footer % {"seq_num": seq_num, "port": port}
	return udata

def ssh_command_pid(host):
	ps_out = subprocess.check_output('ps -ef | grep "ssh ' + host + '"', shell = True)
	pid = map(lambda w: w[1], filter(lambda z: host == z[8], map(lambda y: y.split(), filter(lambda x: ('ssh ' + host) in x, ps_out.split('\n')))))
	if len(pid) > 1:
		logger.info(str(len(pid)) + " ssh processes on host: " + host + ": " + str(pid))
	if len(pid) == 0: return []
	return pid[0]

def find_finished_benchmark(pids):
	finished = []
	while 1:
		time.sleep(5)
		for (i, pid) in pids.values():
			is_alive = len(filter(lambda y: len(y) > 1 and y[1] == pid, map(lambda x: x.split(), subprocess.check_output("ps -ef | grep " + str(pid), shell = True).split('\n'))))
			if not is_alive:
				logger.info("======> VM: " + str(i) + " has finished its execution")
				finished.append(i)
		if len(finished) > 0: break
	return finished

def kill_spec(host):
	ssh_command = "ssh " + host + " 'ps -ef | grep cslab_run'"
	ps_output = subprocess.check_output(ssh_command, shell = True)
	pids = map(lambda z: z[1], filter(lambda y: len(y) > 8 and 'cslab_run_spec' in y[8], map(lambda x: x.split(), ps_output.split("\n"))))
	for pid in pids:
		try:
			child_pid = subprocess.check_output("ssh " + host + " 'pgrep -P " + pid + "'", shell = True)
		except: continue
		os.system("ssh " + host + " 'pkill -P " + child_pid + "'")

def kill_parsec(host):
	ssh_command = "ssh " + host + " 'ps -ef | grep /opt/parsec-benchmark/pkgs'"
	ps_output = subprocess.check_output(ssh_command, shell = True)
	pids = map(lambda z: z[1], filter(lambda y: len(y) > 7 and y[7].startswith('/opt/'), map(lambda x: x.split(), ps_output.split("\n"))))
	for p in pids:
		os.system("ssh " + host + " 'kill -15 " + p + "'")

def kill_tailbench(client):
	ssh_command = "ssh " + client + " 'ps -ef | grep client_run'"
	pids = subprocess.check_output(ssh_command, shell = True)
	pids = map(lambda z: z[1], filter(lambda y: len(y) > 8 and "./client_run.sh" == y[8], map(lambda x: x.split(), pids.split("\n"))))
	for pid in pids:
		try:
			child_pid = subprocess.check_output("ssh " + client + " 'pgrep -P " + pid + "'", shell = True)
		except: continue
		os.system("ssh " + client + " 'kill -15 " + child_pid + "'")

def kill_iperf(host):
	ssh_command = "ssh " + host + " 'ps -ef | grep iperf3'"
	ps_output = subprocess.check_output(ssh_command, shell = True)
	pids = map(lambda z: z[1], filter(lambda y: len(y) > 8 and 'iperf' in y[7], map(lambda x: x.split(), ps_output.split('\n'))))
	for p in pids:
		os.system("ssh " + host + " 'kill -2 " + p + "'")

def verify_empty_host(host):
	pids = ssh_command_pid(host)
	while pids != []:
		logger.info(str(len(pids)) + " ssh connection(s) found on host: " + host + " ...clearing...")
		kill_spec(host)
		kill_parsec(host)
		kill_tailbench('client-1')
		kill_tailbench('client-2')
		kill_iperf(host)
		pids = ssh_command_pid(host)

def run_benchmarks(benchmarks, port):
	hosts = dict()
	pids = dict()
	for (i, benchmark) in enumerate(benchmarks):
		vcpus = benchmark['nr_vcpus']
		host = 'vm' + str(i + 1) + '-' + str(vcpus)
		commands = get_vm_commands(i, benchmark, port, vm_ips[host])
		hosts[i] = host
		verify_empty_host(host)
		if "tailbench" in benchmark['bench'][0] or 'iperf' in benchmark['bench'][0]:
			client_vm = "client-" + str(i + 1)
			verify_empty_host(client_vm)
			server, client = commands.split(sc_split)
			hosts[len(benchmarks) + i] = client_vm
			ssh_server = "ssh " + host + " \'" + server + "\' &"
			ssh_client = "ssh " + client_vm + " \'" + client + "\' &"
			os.system(ssh_server)
			os.system(ssh_client)
			pids[client_vm] = (i, ssh_command_pid(client_vm))
		else:
			ssh_command = "ssh " + host + " \'" + commands + "\' &"
			os.system(ssh_command)
			pids[host] = (i, ssh_command_pid(host))

	finished = find_finished_benchmark(pids)
	if len(list(set(finished))) < 2:
		finished = finished[0]
		host = hosts[finished]
		extra_command = get_vm_commands(finished, benchmarks[finished], port, vm_ips[host], True)
		if "tailbench" in benchmarks[finished]['bench'][0] or 'iperf' in benchmarks[finished]['bench'][0]:
			extra_command, client = extra_command.split(sc_split)
			client_vm = hosts[len(benchmarks) + finished]
			ssh_client = "ssh " + client_vm + " \'" + client + "\' &"
		ssh_command = "ssh " + host + " \'" + extra_command + "\' &"
		os.system(ssh_command)
		if "tailbench" in benchmarks[finished]['bench'][0] or "iperf" in benchmarks[finished]['bench'][0]:
			os.system(ssh_client)
			client_vm = hosts[len(benchmarks) + finished]
			pids[client_vm] = (finished, ssh_command_pid(client_vm))
		else:
			pids[host] = (finished, ssh_command_pid(host))

		while 1:
			extra_fin = find_finished_benchmark(pids)
			if len(list(set(extra_fin))) == 2: break
			extra_fin = extra_fin[0]
			if extra_fin == finished:
				os.system(ssh_command)
				if "tailbench" in benchmarks[finished]['bench'][0] or 'iperf' in benchmarks[finished]['bench'][0]:
					os.system(ssh_client)
					pids[client_vm] = (finished, ssh_command_pid(client_vm))
				else:
					pids[host] = (finished, ssh_command_pid(host))
			else:
				if "spec" in benchmarks[finished]['bench'][0]:
					kill_spec(hosts[finished])
				elif "parsec" in benchmarks[finished]['bench'][0]:
					kill_parsec(hosts[finished])
				elif "tailbench" in benchmarks[finished]['bench'][0]:
					kill_tailbench(hosts[len(benchmarks) + finished])
				elif "iperf" in benchmarks[finished]['bench'][0]:
					kill_iperf(hosts[finished])
				break
	logger.info("Both VMs finished")

if __name__ == "__main__":
	if len(sys.argv) != 5:
		logger.error("Usage: %s <benchmark 1> <vcpus> <benchmark 2> <vcpus>", sys.argv[0])
		sys.exit(1)

	PORT = 8081
	vm_messages_monitor = VmMessagesMonitor(port=PORT)
	vm_messages_monitor.spawn_monitor_thread()
	signal.signal(signal.SIGTERM, signal_handler)
	signal.signal(signal.SIGINT, signal_handler)

	bench_input = [(sys.argv[1], int(sys.argv[2])), (sys.argv[3], int(sys.argv[4]))]

	run_benchmarks(generate_vms_list(bench_input), PORT)

	vm_messages_monitor.stop_monitor_thread()
