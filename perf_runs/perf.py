import sys
sys.path.append('../core/')
from execute import *
sys.path.append('../grid_runs/')
from one_pair import generate_vms_list
import libvirt_client
sys.path.append('/home/ypap/actimanager/common/')
import shell_command

perf_dir = "/home/ypap/measurements-pqos/"

def pin_vcpus(vm, vcpus, node):
	try:
		libvirt_instance_name = getattr(vm, 'OS-EXT-SRV-ATTR:instance_name')
		with libvirt_client.LibVirtConnection(node, 'qemu+ssh') as libvconn:
			libvinstance = libvirt_client.LibVirtInstance(libvconn, str(libvirt_instance_name))
			for vcpu in range(vcpus):
				libvinstance.map_instance_vcpu(vcpu,[vcpu])
		return True
	except:
		logger.info("======> Failed to pin vcpu in pcpus")
		return False

def get_pid_from_vm_id(vm, node):
	command = "nova show %s | grep -i 'OS-EXT-SRV-ATTR:instance_name' | awk -F'|' '{print $3}'" % str(vm.id)
	libvirt_instance_name = shell_command.run_shell_command(command).strip()
	command = "ssh %s ps -ef | grep %s | grep \"qemu-system\" | grep -v grep | awk '{print $2}'" % (node, libvirt_instance_name)
	pid = shell_command.run_shell_command(command).strip()
	return pid

import pprint
def run_perf_vm(vms, node, port, tool):
	if len(vms) > 1:
		logger.info("More than one VM provided, exiting.")
		return
	perf_dir = "/home/ypap/measurements-" + tool + "/"
	logger.info("======> Starting VM")
	vm = vms[0]
	(uuid, vm_instance) = spawn_vm(0, vm, 0, node, port)
	
	logger.info("======> VM started, pinning vcpus" if tool != 'perf' else "======> VM started, starting perf")
	if tool != 'perf':
		ret = pin_vcpus(vm_instance, vm['nr_vcpus'], node)
		logger.info("======> vcpus pinned, starting " + tool)

	output_file = perf_dir + vm['bench'][0] + '-' + str(vm['nr_vcpus']) +".csv"
	
	interval = 1 # seconds, adjust accordingly

	if tool == 'pqos':
		cores = "[0-" + str(vm['nr_vcpus'] - 1) + "]" if vm['nr_vcpus'] - 1 > 0 else "0"
		tool_cmd = "pqos -m all:" + cores + ' -r -o ' + output_file + ' -u csv -i ' + str(interval * 10)
	elif tool == 'pcm':
		cores = ','.join([str(x) for x in range(int(vm['nr_vcpus']))])
		tool_cmd = "/home/ypap/pcm/pcm.x 1 -ns -nsys -yc " + cores + " -csv=" + output_file
	elif tool == 'perf':
		pid = get_pid_from_vm_id(vm_instance, node)
		# For Spanish paper
		#events = "branch-instructions,branch-misses,cycles,instructions,page-faults,context-switches,cpu-migrations,cache-references,cache-misses"
		events = 'instructions,cycles,branch-instructions,branch-misses,LLC-load-misses,LLC-store-misses,dTLB-load-misses,dTLB-store-misses,iTLB-load-misses,L1-dcache-load-misses,L1-icache-load-misses,l2_rqsts.miss'
		tool_cmd = "perf kvm --guest stat -e " + events + " -I " + str(interval * 1000) +\
					" -o " + output_file + " -p " + pid
	ssh_cmd = 'ssh ' + node + ' "' + tool_cmd + '" &'
	os.system(ssh_cmd)
	time.sleep(5)
	remote_pid = subprocess.check_output('ssh ' + node + ' "ps -ef | grep %s"' % tool, shell = True)
	local_pid = subprocess.check_output('ps -ef | grep %s' % tool, shell = True)
	try:
		if tool == 'pqos': lookup = "pqos -m"
		elif tool == 'pcm': lookup = "pcm.x"
		elif tool == 'perf': lookup = "perf kvm"

		remote_pid = int(filter(lambda y: not y == '', \
						 filter(lambda x: lookup in x, remote_pid.split("\n"))[0].split(' '))[1])
		local_pid = int(filter(lambda y: not y == '', \
						filter(lambda x: lookup in x, local_pid.split("\n"))[0].split(' '))[1])
		logger.info("======> %s has started, remote pid is %d, local pid is %d", tool, remote_pid, local_pid)
	except:
		logger.info("==!!==> Did not find pid of %s" % tool)
	if remote_pid == -1:
		logger.info("==!!==> Error, will not be able to kill remote pid")
		kill_str = "ls"
	else:
		kill_str = 'ssh ' + node + ' "kill -2 ' + str(remote_pid) + '"'
	expected_runtime = int(vm['bench'][1]['runtime_isolation'][vm['nr_vcpus']])
	time.sleep(expected_runtime - 5)
	times = 0
	while vm_instance.status == "ACTIVE":
		time.sleep(1)
		vm_instance = ost_client.get_vm(uuid)
		times += 1
		if times > 300:
			logger.info("Stuck VM, exiting.")
			break
	try:
		os.system(kill_str)
	except:
		logger.info("Did not kill remote %s, already finished" % tool)
	try:
		os.kill(local_pid, 15)
	except:
		logger.info("Did not kill local %s, already finished" % tool)

if __name__ == '__main__':
	if len(sys.argv) != 5:
		logger.error("Usage: %s <Benchmark> <vcpus> <node> <tool>", sys.argv[0])
		sys.exit(1)

	tool = sys.argv[4]
	node = sys.argv[3]
	nodeport = int('808' + node[-1])
	ret = ost_client.delete_existing_vms(prefix=node+"-")
	if ret > 0:
		time.sleep(10)

	vm_messages_monitor = VmMessagesMonitor(port=nodeport)
	vm_messages_monitor.spawn_monitor_thread()
	signal.signal(signal.SIGTERM, signal_handler)
	signal.signal(signal.SIGINT, signal_handler)

	bench = sys.argv[1]
	vcpus = int(sys.argv[2])

	vms = generate_vms_list([(bench, vcpus)])

	run_perf_vm(vms, node, nodeport, tool)

	ret = ost_client.delete_existing_vms(prefix= node + "-")
	if ret > 0:
		time.sleep(10)

	vm_messages_monitor.stop_monitor_thread()
	sys.exit(0)

