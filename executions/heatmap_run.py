#!/usr/bin/python
import sys
sys.path.append("../core/")
from vm_messages_monitor import *
from execute import *

vm_header = \
"""export VMUUID=$(basename $(readlink -f /var/lib/cloud/instance)); echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"boot\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d;"""

client_header = \
"""export SUUID=%(suuid)s; export VMUUID=$(basename $(readlink -f /var/lib/cloud/instance)); echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"boot\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d;"""

vm_footer = \
"""echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"shutdown\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d; exit 0"""

vm_calculix = \
"""cd /opt/spec-parsec-benchmarks/spec/; sed -i 's/if "-i" in sys.argv:/if "-i" in sys.argv and not "calculix" in sys.argv[5]:/g' cslab_interpret_spec_cmd.py;"""

vm_spec = \
"""cd /opt/spec-parsec-benchmarks/spec/
for t in `seq 0 $((%(times_to_run)d-1))`; do 
{
	echo "EXECUTION NUMBER $t"
	for i in `seq 0 $((%(vcpus)d-2))`; do
		./cslab_run_specs_static.sh %(bench)s $i &
		sleep 5
	done
	./cslab_run_specs_static.sh %(bench)s $((%(vcpus)d-1))
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"spec-%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
done
"""

vm_parsec = \
"""cd /opt/parsec-benchmark/
source env.sh
for t in `seq 0 $((%(times_to_run)d-1))`; do 
{
	echo "EXECUTION NUMBER $t"
	parsecmgmt -a run -p %(bench)s -i native -n $((%(vcpus)d)) > log/amd64-linux.gcc/run_output.out; tail -n 10 log/amd64-linux.gcc/run_output.out | head -n 1 | ./time_conversion.py
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
done
"""

spec_extra = \
"""cd /opt/spec-parsec-benchmarks/spec/
{
	for i in `seq 0 $((%(vcpus)d-2))`; do
		./cslab_run_specs_static.sh %(bench)s $i &
		sleep 5
	done
	./cslab_run_specs_static.sh %(bench)s $((%(vcpus)d-1))
	wait
} &> /tmp/tosend
"""

parsec_extra = \
"""cd /opt/parsec-benchmark/
source env.sh
{
	parsecmgmt -a run -p %(bench)s -i native -n $((%(vcpus)d)) > log/amd64-linux.gcc/run_output.out
	wait
} &> /tmp/tosend
"""

tailbench_server = \
"""cd /opt/tailbench-v0.9
for t in `seq 0 $((%(times_to_run)d-1))`; do
{
	echo "EXECUTION NUMBER $t"
	./server_run.sh %(bench)s
	wait
} &> /tmp/tosend
done
"""

tailbench_client = \
"""cd /opt/tailbench-v0.9
for t in `seq 0 $((%(times_to_run)d-1))`; do
{
	echo "EXECUTION NUMBER $t"
	./client_run.sh %(bench)s %(ip)s
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$SUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"tailbench.%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
done
"""
tailbench_client_extra = \
"""cd /opt/tailbench-v0.9
{
	echo "EXECUTION NUMBER +1"
	./client_run.sh %(bench)s %(ip)s
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$SUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"tailbench.%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
"""

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
	else:
		logger.info("Spawned new VM with seq_num: %d and name: %s", seq_num, vm_name)
		udata = vm_header % {"seq_num": seq_num, "port": port}
		if "spec-" in bench_name:
	#		if "calculix" in bench_name: udata += vm_calculix
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
		udata += vm_footer % {"seq_num": seq_num, "port": port}
	return udata

def ssh_command_pid(host):
	ps_out = subprocess.check_output('ps -ef | grep "ssh ' + host + '"', shell = True)
	pid = map(lambda w: w[1], filter(lambda z: host == z[8], map(lambda y: y.split(), filter(lambda x: ('ssh ' + host) in x, ps_out.split('\n')))))
	if len(pid) > 1:
		logger.info(str(len(pid)) + " ssh processes on host: " + host + ": " + str(pid))
	return pid[0]

def find_finished_benchmark(pids):
	finished = []
	while 1:
		time.sleep(5)
		for (i, pid) in pids.values():
			is_alive = len(filter(lambda y: len(y) > 1 and y[1] == pid, map(lambda x: x.split(), subprocess.check_output("ps -ef | grep " + pid, shell = True).split('\n'))))
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

def kill_tailbench():
	ssh_command = "ssh client 'ps -ef | grep client_run'" 
	pids = subprocess.check_output(ssh_command, shell = True)
	pids = map(lambda z: z[1], filter(lambda y: len(y) > 8 and "./client_run.sh" == y[8], map(lambda x: x.split(), pids.split("\n"))))
	for pid in pids:
		try:
			child_pid = subprocess.check_output("ssh client 'pgrep -P " + pid + "'", shell = True)
		except: continue
		os.system("ssh client 'kill -15 " + child_pid + "'")

def run_benchmarks(benchmarks, port):
	hosts = list()
	pids = dict()
	for (i, benchmark) in enumerate(benchmarks):
		vcpus = benchmark['nr_vcpus']
		host = 'vm' + str(i + 1) + '-' + str(vcpus)
		commands = get_vm_commands(i, benchmark, port, vm_ips[host])
		hosts.append(host)
		if "tailbench" in benchmark['bench'][0]:
			server, client = commands.split("|sc|")
			hosts.append("client")
			ssh_server = "ssh " + host + " \'" + server + "\' &"
			ssh_client = "ssh client \'" + client + "\' &"
			os.system(ssh_server)
			os.system(ssh_client)
			pids["client"] = (i, ssh_command_pid("client"))
		else:
			ssh_command = "ssh " + host + " \'" + commands + "\' &"
			os.system(ssh_command)
			pids[host] = (i, ssh_command_pid(host))

	finished = find_finished_benchmark(pids)
	if len(list(set(finished))) < 2:
		finished = finished[0]
		host = hosts[finished]
		extra_command = get_vm_commands(finished, benchmarks[finished], port, vm_ips[host], True)
		if "tailbench" in benchmarks[finished]['bench'][0]:
			extra_command, client = extra_command.split(sc_split)
			ssh_client = "ssh client \'" + client + "\' &"
		ssh_command = "ssh " + host + " \'" + extra_command + "\' &"
		os.system(ssh_command)
		if "tailbench" in benchmarks[finished]['bench'][0]:
			os.system(ssh_client)
			pids["client"] = (finished, ssh_command_pid("client"))
		else:
			pids[host] = (finished, ssh_command_pid(host))

		while 1:
			extra_fin = find_finished_benchmark(pids)
			if len(list(set(extra_fin))) == 2: break
			extra_fin = extra_fin[0]
			if extra_fin == finished:
				os.system(ssh_command)
				if "tailbench" in benchmarks[finished]['bench'][0]:
					os.system(ssh_client)
					pids["client"] = (finished, ssh_command_pid("client"))
				else:
					pids[host] = (finished, ssh_command_pid(host))
			else:
				if "spec" in benchmarks[finished]['bench'][0]:
					kill_spec(hosts[finished])
				elif "parsec" in benchmarks[finished]['bench'][0]:
					kill_parsec(hosts[finished])
				elif "tailbench" in benchmarks[finished]['bench'][0]:
					kill_tailbench()
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
