import sys
sys.path.append('../core/')
from execute import *
sys.path.append('../grid_runs/')
from one_pair import generate_vms_list
import libvirt_client
sys.path.append('/home/ypap/actimanager/common/')
import shell_command

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

def run_attacker(vms, node, port, att):
	if len(vms) > 1:
		logger.info("More than one VM provided, exiting.")
		return

	logger.info("======> Starting VM")
	vm = vms[0]
	(uuid, vm_instance) = spawn_vm(0, vm, 0, node, port)
	expected_runtime = int(vm['bench']['runtime_isolation'])
	
	ret = pin_vcpus(vm_instance, vm['nr_vcpus'], node)
	logger.info("======> VM started, vcpus pinned, starting attacker " + att)

	tool_cmd = "/home/ypap/iBench/src/" + att + " " + str(2 * expected_runtime)

	ssh_cmd = 'ssh ' + node + ' "' + tool_cmd + '" &'
	os.system(ssh_cmd)
	time.sleep(5)
	remote_pid = subprocess.check_output('ssh ' + node + ' "ps -ef | grep %s"' % att, shell = True)
	local_pid = subprocess.check_output('ps -ef | grep %s' % att, shell = True)
	try:
		lookup = "src/" + att

		remote_pid = int(filter(lambda y: not y == '', \
						 filter(lambda x: lookup in x, remote_pid.split("\n"))[0].split(' '))[1])
		local_pid = int(filter(lambda y: not y == '', \
						filter(lambda x: lookup in x, local_pid.split("\n"))[0].split(' '))[1])
		pin_cmd = 'ssh ' + node + ' "taskset -pc 9 ' + str(remote_pid) + '"'
		os.system(pin_cmd)
		logger.info("======> %s has started, remote pid is %d, local pid is %d", att, remote_pid, local_pid)
	except:
		logger.info("      > Did not find pid of %s" % att)
	if remote_pid == -1:
		logger.info("      > Error, will not be able to kill remote pid")
		kill_str = "ls"
	else:
		kill_str = 'ssh ' + node + ' "kill -2 ' + str(remote_pid) + '"'
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

	run_attacker(vms, node, nodeport, tool)

	ret = ost_client.delete_existing_vms(prefix= node + "-")
	if ret > 0:
		time.sleep(10)

	vm_messages_monitor.stop_monitor_thread()
	sys.exit(0)

