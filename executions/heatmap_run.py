#!/usr/bin/python
import sys
sys.path.append("../core/")
from vm_messages_monitor import *
from execute import *
from one_pair import generate_vms_list

vm_ip = {1: {1: "33", 2: "51", 4: "45", 8: "55"},
		 2: {1: "39", 2: "32", 4: "37", 8: "31"}}
vm_uuid = {1: {1: "8e4df141-d077-4dd8-b4ce-8ca9ea25d761"}}

vm_header = \
"""export VMUUID=$(basename $(readlink -f /var/lib/cloud/instance)); echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"boot\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d;"""

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
for t in `seq 0 0`; do
{
	for i in `seq 0 $((%(vcpus)d-2))`; do
		./cslab_run_specs_static.sh %(bench)s $i &
		sleep 5
	done
	./cslab_run_specs_static.sh %(bench)s $((%(vcpus)d-1))
	wait
} &> /tmp/tosend
done
"""

parsec_extra = \
"""cd /opt/parsec-benchmark/
source env.sh
for t in `seq 0 0`; do
{
	parsecmgmt -a run -p %(bench)s -i native -n $((%(vcpus)d)) > log/amd64-linux.gcc/run_output.out
	wait
} &> /tmp/tosend
done
"""

def get_vm_commands(seq_num, vm_chars, port, fill_in = False):
	vcpus = vm_chars['nr_vcpus']
	bench = vm_chars['bench']
	runtime = vm_chars['runtime']

	runtime_isolation = bench[1]['runtime_isolation'][vcpus]
	times_to_run = int(math.ceil((runtime * 60.0) / runtime_isolation))

	bench_name = bench[0]
	vm_name = bench_name.replace('.','-') if "parsec" in bench_name else bench_name
	vm_name = '-'.join(["acticloud1", "gold", vm_name, str(times_to_run) + "_times", "to_completion"])
	logger.info("Spawned new VM with seq_num: %d and name: %s", seq_num, vm_name)
	udata = ""
	
	if not fill_in:
		udata = vm_header % {"seq_num": seq_num, "port": port}
	if "spec-" in bench_name:
#		if "calculix" in bench_name:
#			udata += vm_calculix
		spec_bench = bench_name.split('-')[1]
		if fill_in:
			udata += spec_extra % {"bench": spec_bench, "vcpus": vcpus}
		else:
			udata += vm_spec % {"seq_num": seq_num, "vcpus": vcpus,
								"times_to_run": times_to_run, "bench": spec_bench, "port": port}
	elif "parsec" in bench_name:
		if fill_in:
			udata += parsec_extra % {"bench": bench_name, "vcpus": vcpus}
		else:
			udata += vm_parsec % {"seq_num": seq_num, "vcpus": vcpus,
								  "times_to_run": times_to_run, "bench": bench_name, "port": port}
	if not fill_in:
		udata += vm_footer % {"seq_num": seq_num, "port": port}
	return udata

def find_finished_benchmark(ips):
	finished = []
	while 1:
		time.sleep(1)
		for (i, ip) in enumerate(ips):
			check = subprocess.check_output('ps -ef | grep "10.0.100.' + ip + '"', shell = True)
			try:
				check = int(filter(lambda x: 'ssh ubuntu' in x, check.split('\n'))[0].split()[1])
			except:
				logger.info("======> VM: " + str(i) + " has finished its execution")
				finished.append(i)
		if len(finished) > 0: break
	return finished

def kill_spec(ip):
	ssh_command = "ssh ubuntu@10.0.100." + ip + " 'ps -ef | grep cslab_run'"
	ps_output = subprocess.check_output(ssh_command, shell = True).split('\n')
	pids = []
	for row in ps_output:
		row = row.split()
		if len(row) < 9: continue
		if 'cslab_run_spec' in row[8]:
			pids.append(row[1])
	for p in pids:
		pgrep_command = "ssh ubuntu@10.0.100." + ip + " 'pgrep -P " + p + "'"
		child_pid = subprocess.check_output(pgrep_command, shell = True)
		kill_command = "ssh ubuntu@10.0.100." + ip + " 'pkill -P " + child_pid + "'"
		os.system(kill_command)

def kill_parsec(ip):
	ssh_command = "ssh ubuntu@10.0.100." + ip + " 'ps -ef | grep /opt/parsec-benchmark/pkgs'"
	ps_output = subprocess.check_output(ssh_command, shell = True).split('\n')
	pids = []
	for row in ps_output:
		row = row.split()
		if len(row) < 8: continue
		if row[7].startswith('/opt/'):
			pids.append(row[1])
	for p in pids:
		kill_command = "ssh ubuntu@10.0.100." + ip + " 'kill -15 " + p + "'"
		os.system(kill_command)

def run_benchmarks(benchmarks, port):
	ips = []
	for (i, benchmark) in enumerate(benchmarks):
		commands = get_vm_commands(i, benchmark, port)
		vcpus = benchmark['nr_vcpus']
		ip = vm_ip[i + 1][vcpus]
		ips.append(ip)
		ssh_command = "ssh ubuntu@10.0.100." + ip + " \'" + commands + "\' &"
		os.system(ssh_command)
	finished = find_finished_benchmark(ips)
	if len(finished) < 2:
		finished = finished[0]
		extra_command = get_vm_commands(finished, benchmarks[finished], port, True)
		ip = vm_ip[finished + 1][benchmarks[finished]['nr_vcpus']]
		ssh_command = "ssh ubuntu@10.0.100." + ip + " \'" + extra_command + "\' &"
		os.system(ssh_command)
		while 1:
			extra_fin = find_finished_benchmark(ips)
			if len(extra_fin) == 2: break
			extra_fin = extra_fin[0]
			if extra_fin == finished:
				os.system(ssh_command)
				logger.info("======> VM: " + str(extra_fin) + " restarted as extra")
			else:
				if "spec" in benchmarks[finished]['bench'][0]:
					kill_spec(ips[finished])
				elif "parsec" in benchmarks[finished]['bench'][0]:
					kill_parsec(ips[finished])
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

	bench1 = sys.argv[1]
	vcpus1 = int(sys.argv[2])
	bench2 = sys.argv[3]
	vcpus2 = int(sys.argv[4])
	bench_input = [(bench1, vcpus1), (bench2, vcpus2)]

	run_benchmarks(generate_vms_list(bench_input), PORT)

	vm_messages_monitor.stop_monitor_thread()
