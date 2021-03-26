import sys
sys.path.append("core/")
from execute import *

def generate_vms_list(bench_input):
	is_gold = 1
	benchmarks = list()
	vms = list()
	for (bench_name, vcpus) in bench_input:
		bench = [x for x in benches if bench_name in x["name"]]

		if len(bench) != 1:
			logger.error("Error in benchmark name: %s", bench_name)
			signal_handler(0, 0)
		benchmarks.append((bench[0], vcpus))

	runtime = int(math.ceil(max([b[0]['runtime_isolation'] for b in benchmarks]) / 60.0))
	for (benchmark, vcpus) in benchmarks:
		vm = dict()
		vm['nr_vcpus'] = vcpus
		vm['is_gold'] = is_gold
		vm['is_noisy'] = benchmark['is_noisy']
		vm['is_sensitive'] = benchmark['is_sensitive']
		vm['bench'] = benchmark
		vm['runtime'] = runtime
		vms.append(vm)
	return vms

def unfinished(vm_uuids):
	ret = False
	for i in vm_uuids:
		try:
			vm_instance = ost_client.get_vm(i)
			is_active = vm_instance.status == "ACTIVE"
		except:
			continue
		ret = ret or is_active
	return ret

def wait_to_finish(vm_uuids, runtime):
	sec30 = 0
	max_wait = runtime * 5
	while unfinished(vm_uuids):
		time.sleep(30)
		sec30 += 0.5
		if sec30 > max_wait:
			logger.info("Stuck VM, exiting...")
			break

def run_benchmarks(vms, node, port, seq_num = 0, wait = True):
	vm_uuids = []
	for (i, vm_chars) in enumerate(vms):
		uuid = spawn_vm(seq_num * len(vms) + i, vm_chars, 0, node, port)
		vm_uuids.append(uuid[0])
	for i in vm_uuids:
		logger.info("=> VM with uuid %s is active", i)
	
	if wait:
		wait_to_finish(vm_uuids, max([vm['runtime'] for vm in vms]))
	return vm_uuids

if __name__ == '__main__':
	if len(sys.argv) != 6:
		logger.error("Usage: %s <Benchmark 1> <vcpus> <Benchmark 2> <vcpus> <node>", sys.argv[0])
		sys.exit(1)

	node = sys.argv[5]
	ret = ost_client.delete_existing_vms(prefix=node + "-")
	logger.info("%d VMs to be deleted.", ret)
	if ret > 0:
		time.sleep(10)

	CUSTOM_PORT = int("808" + node[-1])
	CUSTOM_PORT = 8080

	vm_messages_monitor = VmMessagesMonitor(port=CUSTOM_PORT)
	vm_messages_monitor.spawn_monitor_thread()
	signal.signal(signal.SIGTERM, signal_handler)
	signal.signal(signal.SIGINT, signal_handler)

	bench1 = sys.argv[1]
	vcpus1 = int(sys.argv[2])
	bench2 = sys.argv[3]
	vcpus2 = int(sys.argv[4])
	bench_input = [(bench1, vcpus1), (bench2, vcpus2)]
	vms = generate_vms_list(bench_input)

	run_benchmarks(vms, node, CUSTOM_PORT)

	ret = ost_client.delete_existing_vms(prefix=node + '-')
	logger.info("%d VMs to be deleted.", ret)
	if ret > 0:
		time.sleep(10)

	vm_messages_monitor.stop_monitor_thread()
	sys.exit(0)
