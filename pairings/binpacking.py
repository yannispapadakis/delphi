#!/usr/bin/python3
from pairing import *
MAX_VCPUS = 10

def get_heatmap(benchmarks, version):
	if version == 'r': use_heatmap = heatmap
	else:
		use_heatmap = spawn_heatmap()
		read_heatmap(use_heatmap, 'pred_heatmap')
	window = dict()
	for bench1 in benchmarks:
		window[bench1] = dict()
		for bench2 in set(benchmarks).difference([bench1]):
			try: window[bench1][bench2] = use_heatmap[bench1.split(',')[1]][bench2.split(',')[1]]
			except: window[bench1][bench2] = 0
	return window

def violations_counter(bins, preds, alg):
	def name(b): return b.split(',')[1]
	def slo(b): return float(b.split(',')[-1])
	violations = 0
	for b in bins:
		if alg == 'delphi':
			tuples = list(map(lambda x: (x[1], x[2]), senscont(b,preds)))
			if len(b) == 1: print(f"{tuples[0]} {b[0]}")
			if len(b) == 2:
				violations += int(heatmap[name(b[0])][name(b[1])] > slo(b[0])) + int(heatmap[name(b[1])][name(b[0])] > slo(b[1]))
				print(f"{tuples[0]} {b[0]}{' '*(27 - len(b[0]))}{tuples[1]} {b[1]}{' ' * (27 - len(b[1]))}{heatmap[name(b[0])][name(b[1])]:.2f} - {heatmap[name(b[1])][name(b[0])]:.2f}  {violations}")
			if len(b) >= 3:
				#run the benchmarks
				print(len(b), b)
		else:
			if len(b) == 1: print(f"{b[0]}")
			if len(b) == 2:
				violations += int(heatmap[name(b[0])][name(b[1])] > slo(b[0])) + int(heatmap[name(b[1])][name(b[0])] > slo(b[1]))
				print(f"{b[0]}{' '*(27 - len(b[0]))}{b[1]}{' ' * (27 - len(b[1]))}{heatmap[name(b[0])][name(b[1])]:.2f} - {heatmap[name(b[1])][name(b[0])]:.2f}  {violations}")
			if len(b) >= 3: print(len(b), b)
	print(f"Bins used: {len(bins)} with {violations} violations")

def slowdown(benchmarks, heatmap):
	# Pythia implementation here
	return list(map(lambda x: (x, float(x.split(',')[-1]) - sum([heatmap[x][y] for y in set(benchmarks).difference([x])])), benchmarks))

def tuples(benchmarks, preds):
	return list(map(lambda x: (x, (preds[x]['sens'], sum([preds[y]['cont'][preds[x]['slo']] for y in set(benchmarks).difference([x])]))), benchmarks))

def senscont(benchmarks, preds): return list(map(lambda x: (x, preds[x]['sens'], preds[x]['cont'][1.2]), benchmarks))
	
def vcpus(benchmark): return int(benchmark.split(',')[1][-1])

sens_factor = 2
c = 2
def cs_sum(b):
	def s_sum(b): return sens_factor * sum([y[1][0] for y in b])
	def c_sum(b): return sum([y[1][1] for y in b])
	return (s_sum(b), c_sum(b))

def find_fitting_bins(benchmark, bins, alg, preds):
	vcpus_fit = list(filter(lambda x: vcpus(benchmark) + sum(map(vcpus, x)) <= MAX_VCPUS, bins))
	if vcpus_fit == []: 
		bins.append([benchmark])
	else:
		if alg == 'heatmap':
			sd_bins = [slowdown(b + [benchmark], preds) for b in vcpus_fit]
			best_fit = list(filter(lambda x: all([y[1] > 0 for y in x]), sd_bins))
			if best_fit == []:
				bins.append([benchmark])
			else:
				best_bin = min(best_fit, key = lambda x: min([y[1] for y in x]))
				bins[bins.index([x[0] for x in best_bin if x[0] != benchmark])].append(benchmark)
		if alg == 'delphi':
			t_bins = [tuples(b + [benchmark], preds) for b in vcpus_fit]
			best_fit = list(filter(lambda x: all([0 in y[1] for y in x]), t_bins))
			if best_fit == []:
				bins.append([benchmark])
			else:
				sum_filter = list(filter(lambda x: (c == 2 and len(x) == 2) or all([y < len(x) + c - 2 for y in cs_sum(x)]), best_fit))
				if sum_filter == []:
					bins.append([benchmark])
				else:
					min_length = min(len(b) for b in sum_filter)
					min_len = list(filter(lambda x: len(x) == min_length, sum_filter))
					best_bin = max(min_len, key = lambda x: sum(cs_sum(x)))
					bins[bins.index([x[0] for x in best_bin if x[0] != benchmark])].append(benchmark)
		if alg == 'random':			
			bins[bins.index(max(vcpus_fit, key = lambda x: sum(map(vcpus,x))))].append(benchmark)

def best_fit_bin_packing(benchmarks, alg):
	benchmarks = sorted(benchmarks, key = vcpus, reverse = True)
	preds = []
	if alg == 'heatmap':
		preds = get_heatmap(benchmarks, 'r')
		benchmarks = sorted(benchmarks, key = lambda x: np.mean(list(preds[x].values())), reverse = True)
	elif alg == 'delphi':
		preds = get_predictions(benchmarks, 'r', 2)
		benchmarks = sorted(benchmarks, key = lambda x: (preds[x]['sens'], sum(preds[x]['cont'].values())), reverse = True)
	bins = []
	for (i, benchmark) in enumerate(benchmarks):
		find_fitting_bins(benchmark, bins, alg, preds)
	violations_counter(bins, preds, alg)

def calculate_bins(args):
	arg_check_bp(args)
	(contention, size, qos_in, classes_workload) = ('m', 100, '1.2', 2)
	#benchmarks = generate_workload(contention, size, qos_in, classes_workload, printed)
	with open(workload_filename(contention, size, qos_in), 'r') as workload_fd:
		bench_list = [row for row in csv.reader(workload_fd)]
	benchmarks = list(set([f"{i},{row[0]},{row[1]}" for (i, row) in enumerate(bench_list)]))
	best_fit_bin_packing(benchmarks, args[1])

def arg_check_bp(args):
	if args[1] not in ['heatmap', 'delphi', 'random']: sys.exit(1)

if __name__ == '__main__':
	calculate_bins(sys.argv)
