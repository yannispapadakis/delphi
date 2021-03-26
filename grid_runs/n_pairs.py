import sys, csv, random
sys.path.append("../core/")
from execute import *
from one_pair import *
from collections import OrderedDict
sys.path.append("../algorithms/")
from algo_pairing import *

TIMES = 5
PAIRS_PER_NODE = 2

def generate_vms_pairs(bench_file):
	is_gold = 1
	fd = open(bench_file)
	reader = csv.reader(fd, delimiter=',')
	benchmarks = [row[0] + '-' + row[1] for row in reader]
	if len(benchmarks) % 2:
		benchmarks.append(benchmarks[0])
	
	benchmarks = decide_pairs(benchmarks, 'oracle')

	vms = []
	for pair in benchmarks:
		runtimes = []
		bench_pair = []
		for b in pair:
			(benchmark, vcpus) = b.split('-')
			bench = [x for x in benches if benchmark in x["name"]]

			if len(bench) != 1:
				logger.error("Error in benchmark name: %s", bench_name)
				signal_handler(0, 0)
			bench = bench[0]
			if int(vcpus) not in [1, 2, 4, 8]:
				logger.error("Error in vcpus of benchmark %s: %s", bench_name, vcpus)
				signal_handler(0, 0)
			runtimes.append(math.ceil(TIMES * int(bench['runtime_isolation'])) / 60.0)
			bench_pair.append((bench, int(vcpus)))
			
		runtime = int(max(runtimes))
		vm_pair = []
		for b in bench_pair:
			vm = dict()
			vm['nr_vcpus'] = b[1]
			vm['is_gold'] = is_gold
			vm['is_noisy'] = b[0]['is_noisy']
			vm['is_sensitive'] = b[0]['is_sensitive']
			vm['bench'] = b[0]
			vm['runtime'] = runtime
			vm_pair.append(vm)
		vms.append(vm_pair)
	return vms

def delete_pair(vm_uuids):
	for uuid in vm_uuids:
		try:
			vm = ost_client.get_vm(uuid)
			ost_client.nova.servers.delete(vm)
		except:
			logger.error("|||||| Could not delete vm with id: %s", uuid)

def wait_for_any_pair(pairs):
	while 1:
		for node in pairs:
			active_vms = pairs[node]
			for (uuids, runtime) in active_vms:
				if not unfinished(uuids):
					logger.info("|||||| Finished pair: %s at node: %s", str(uuids), node)
					delete_pair(uuids)
					return node
			time.sleep(20)

def run_pairs(pairs, nodes, port):
	active_pairs = OrderedDict()
	for node in nodes:
		active_pairs[node] = []
	for (i, pair) in enumerate(pairs):
		for node in nodes:
			deleted = count_and_delete_finished_vms(node)
			active_pairs[node] = [x for x in active_pairs[node] if unfinished(x[0])]
		actives = map(lambda x: (x[0], len(x[1])), active_pairs.items())
		valid_nodes = filter(lambda x: x[1] < PAIRS_PER_NODE, actives)
		while len(valid_nodes) < 1:
			logger.info("|||||| Waiting for any pair to finish...")
			node = wait_for_any_pair(active_pairs)
			for n in nodes:
				active_pairs[n] = [x for x in active_pairs[n] if unfinished(x[0])]
			actives = map(lambda x: (x[0], len(x[1])), active_pairs.items())
			valid_nodes = filter(lambda x: x[1] < PAIRS_PER_NODE, actives)
		sel_node = min(valid_nodes, key = lambda x: x[1])[0]
		logger.info("|||||| Node Selected: (from delete:) %s (from dict:) %s", node, sel_node)
		logger.info("|||||| Active pairs per node: %s", str(actives))
		vm_uuids = run_benchmarks(pair, sel_node, port, i, i == (len(pairs) - 1))
		pair_runtime = max([vm['runtime'] for vm in pair]) * TIMES
		active_pairs[sel_node].append((vm_uuids, pair_runtime))
	vm_uuids = [uuid for pair in [p[0] for p in active_pairs.values()] for uuid in pair]
	runtime = [x[1] for x in active_pairs.values()]
	wait_to_finish(vm_uuids, runtime)

if __name__ == '__main__':
	if len(sys.argv) != 3:
		logger.error("Usage: %s <benchmarks file> <nodes>", sys.argv[0])
		sys.exit(1)
	
	benchmarks_file = '/home/ypap/actimanager/workload/workload_pairs/' + sys.argv[1]
	nodes = map(lambda x: 'acticloud'+x, sys.argv[2].split(','))

	nodes = ['acticloud3', 'acticloud4']
	for node in nodes:
		ret = ost_client.delete_existing_vms(prefix = node + '-')
		if ret > 0:
			time.sleep(10)

	net_port = 8084
	
	vm_messages_monitor = VmMessagesMonitor(port = net_port)
	vm_messages_monitor.spawn_monitor_thread()
	signal.signal(signal.SIGTERM, signal_handler)
	signal.signal(signal.SIGINT, signal_handler)

	pairs = generate_vms_pairs(benchmarks_file)
	run_pairs(pairs, nodes, net_port)

	for node in nodes:
		ret = ost_client.delete_existing_vms(prefix = node + '-')
		if ret > 0:
			time.sleep(10)
	vm_messages_monitor.stop_monitor_thread()
