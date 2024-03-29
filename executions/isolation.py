#!/usr/bin/python
import sys
sys.path.append("../core/")
from benchmarks import *

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

def run_shell_command(command):
	process = subprocess.Popen(command, stdout=subprocess.PIPE,
	                                    stderr=subprocess.PIPE, shell=True)
	time.sleep(2)
	out, err = process.communicate()
	time.sleep(2)
	process.wait()
	return out

def get_vm_commands(bench, port, ip, vcpus = 0):
	bench_name = bench[0]
	vm_name = bench_name.replace('.','-') if "parsec" in bench_name else bench_name
	vm_name = '-'.join(["acticloud1", "gold", vm_name, "1_times", "to_completion"])
	vcpus = bench[2]
	udata = ""
	
	logger.info("Spawned new VM with seq_num: 0 and name: %s", vm_name)
	udata = vm_header % {"port": port, "seq_num": 0}
	if "spec-" in bench_name:
		spec_bench = bench_name.split('-')[1]
		udata += vm_spec % {"vcpus": vcpus, "times_to_run": 1, "seq_num": 0,
							"bench": spec_bench, "port": port}
	elif "parsec" in bench_name:
		udata += vm_parsec % {"vcpus": vcpus, "times_to_run": 1, "seq_num": 0,
							  "bench": bench_name, "port": port}
	elif "tailbench" in bench_name:
		udata += tailbench_server % {"times_to_run": 1, "bench": bench_name.split('.')[1]}
		udata += vm_footer % {"port": port, "seq_num": 0}
		udata += sc_split
		suuid = subprocess.check_output("ssh root@10.0.100." + ip + " 'echo $(basename $(readlink -f /var/lib/cloud/instance))'", shell = True)[:-1]
		udata += client_header % {"suuid": suuid, "port": port, "seq_num": 0}
		udata += tailbench_client % {"vcpus": vcpus, "ip": ip, "times_to_run": 1, "seq_num": 0,
									 "bench": bench_name.split('.')[1], "port": port}
	elif "iperf" in bench_name:
		udata += iperf_server % {"times_to_run": 1, 'seq_num': 0, 'port': port}
		udata += vm_footer % {'port': port, "seq_num": 0}
		udata += sc_split
		suuid = subprocess.check_output("ssh root@10.0.100." + ip + " 'echo $(basename $(readlink -f /var/lib/cloud/instance))'", shell = True)[:-1]
		udata += client_header % {"suuid": suuid, "port": port, "seq_num": 0}
		udata += iperf_client % {"times_to_run": 1, "ip": ip}
	udata += vm_footer % {"port": port, "seq_num": 0}
	if vcpus > 0: return (udata, benches_vcpus[bench_name]['runtime_isolation'][vcpus])
	return udata

def ssh_command_pid(host):
	ps_out = subprocess.check_output('ps -ef | grep "ssh ' + host + '"', shell = True)
	pid = map(lambda w: w[1], filter(lambda z: host == z[8], map(lambda y: y.split(), filter(lambda x: ('ssh ' + host) in x, ps_out.split('\n')))))
	if len(pid) > 1:
		logger.info(str(len(pid)) + " ssh processes on host: " + host + ": " + str(pid))
	return pid[0]

def wait_for_benchmark(pid):
	while 1:
		time.sleep(5)
		is_alive = len(filter(lambda y: len(y) > 1 and y[1] == pid, map(lambda x: x.split(), subprocess.check_output("ps -ef | grep " + pid, shell = True).split('\n'))))
		if not is_alive: break

def vm_pid(ip):
	uuid = subprocess.check_output("ssh root@10.0.100." + ip + " 'echo $(basename $(readlink -f /var/lib/cloud/instance))'", shell = True)[:-1]
	command = "nova show %s | grep -i 'OS-EXT-SRV-ATTR:instance_name' | awk -F'|' '{print $3}'" % str(uuid)
	libvirt_instance_name = run_shell_command(command).strip()
	command = "ps -ef | grep %s | grep \"qemu-system\" | grep -v grep | awk '{print $2}'" % (libvirt_instance_name)
	pid = run_shell_command(command).strip()
	return pid

def execute_perf(tool, ip, runtime):
	perf_dir = "/home/ypap/measurements-" + tool + '/'
	output_file = perf_dir + bench[0] + '-' + str(bench[2]) + '.csv'
	interval = 1

	if tool == 'pqos':
		cores = "[0-" + str(bench[2] - 1) + "]" if bench[2] > 1 else "0"
		tool_cmd = "pqos -m all:%(cores)s -r -o %(output)s -u csv -i %(int)s &" \
				   % {"cores": cores, "output": output_file, "int": str(interval * 10)}
	elif tool == "perf":
		pid = vm_pid(ip)
		events = 'instructions,cycles,branch-instructions,branch-misses,' + \
				 'LLC-load-misses,LLC-store-misses,dTLB-load-misses,' + \
				 'dTLB-store-misses,iTLB-load-misses,' + \
				 'L1-dcache-load-misses,L1-icache-load-misses,l2_rqsts.miss'
		#events = 'branch-instructions,branch-misses,cycles,instructions,page-faults,context-switches,cpu-migrations,cache-references,cache-misses'
		tool_cmd = "perf kvm --guest stat -e %(events)s -I %(int)s -o %(output)s -p %(pid)s &" \
				   % {"events": events, "int": str(interval * 1000), "pid": pid, "output": output_file}
	else: # attackers
		tool_cmd = "/home/ypap/iBench/src/%(tool)s %(runtime)s &" \
					% {"tool": tool, "runtime": str(3 * runtime)}
	os.system(tool_cmd)
	tool_pid = subprocess.check_output("ps -ef | grep '%s'" % tool, shell = True)
	try:
		tool_pid = int(map(lambda x: x[1], \
					   filter(lambda x: len(x) > 7 and tool in x[7], \
					   map(lambda x: x.split(), tool_pid.split("\n"))))[0])
		logger.info("======> %s has started, PID: %d", tool, tool_pid)
		if not tool.startswith('p') and not tool.startswith('c'): os.system("taskset -pc 9 " + str(tool_pid))
		return tool_pid
	except:
		logger.info("! Did not find PID of %s at host" % tool)

def kill_perf(tool, tool_pid):
	try:
		os.kill(tool_pid, 15)
		logger.info("======> %s stopped (PID: %d)", tool, tool_pid)
	except:
		try:
			grep = subprocess.check_output('ps -ef | grep "perf kvm"', shell=True)
			pid = int(filter(lambda x: 'perf kvm --guest' in x, grep.split('\n'))[0].split()[1])
			os.kill(pid, 15)
			logger.info("======> %s stopped -via grep- (PID: %d)", tool, pid)
		except:
			logger.info("Did not kill local %s, already finished" % tool)

def isolation_run(bench, port, tool):
	host = 'vm1-' + str(bench[2])
	commands = get_vm_commands(bench, port, vm_ips[host], bench[2] if not tool.startswith('p') else 0)
	runtime = 1
	if not tool.startswith('p'): (commands, runtime) = commands
	tool_pid = execute_perf(tool, vm_ips[host], runtime)

	if "tailbench" in bench[0] or "iperf" in bench[0]:
		server, client = commands[0].split(sc_split)
		ssh_server = "ssh " + host + " \'" + server + "\' &"
		ssh_client = "ssh client-1 \'" + client + "\' &"
		os.system(ssh_server)
		os.system(ssh_client)
	else:
		ssh_command = "ssh " + host + " \'" + commands[0] + "\' &"
		os.system(ssh_command)
	pid = ssh_command_pid('client-1' if 'tailbench' in bench[0] or 'iperf' in bench[0] else host)

	wait_for_benchmark(pid)
	kill_perf(tool, tool_pid)

if __name__ == "__main__":
	if len(sys.argv) != 4:
		logger.error("Usage: %s <benchmark> <vcpus> <tool>", sys.argv[0])
		sys.exit(1)
	
	PORT = 8081
	vm_messages_monitor = VmMessagesMonitor(port=PORT)
	vm_messages_monitor.spawn_monitor_thread()
	signal.signal(signal.SIGTERM, signal_handler)
	signal.signal(signal.SIGINT, signal_handler)

	bench = list(filter(lambda x: sys.argv[1] in x[0], benches_vcpus.items())[0]) + \
			[int(sys.argv[2])]
	isolation_run(bench, PORT, sys.argv[3])

	vm_messages_monitor.stop_monitor_thread()	
