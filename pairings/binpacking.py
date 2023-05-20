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

def group_results(n, preds):
	total_measures = parse_files(f"/home/ypap/delphi/results/{n}ads/")
	results = dict()

	for f in total_measures.keys():
		f = f.replace('img-dnn', 'imgdnn')
		benches = list(map(lambda x: x.replace('_', '-'), f.split('.txt')[0].split('-')))
		benches = list(map(lambda x: x.replace('imgdnn', 'img-dnn'), benches))
		f = f.replace('imgdnn', 'img-dnn')
		perfs = total_measures[f]['vm_mean_perf']
		batch_pred = str(sorted(list(map(lambda x: preds[x], benches))))
		for (i, bench) in enumerate(benches):
			pred = str(preds[bench])
			if pred not in results: results[pred] = {batch_pred: [perfs[i]]}
			else:
				if batch_pred not in results[pred]: results[pred][batch_pred] = [perfs[i]]
				else: results[pred][batch_pred].append(perfs[i])
	return results

def probabilities(triple, cl, preds, results):
	violations = []
	for bench in triple:
		runs = results[str(preds[bench])][str(sorted(list(map(lambda x: preds[x], triple))))]
		prob = 100 * len(list(filter(lambda x: x < 1.2, runs))) / float(len(runs))
		violations.append(random.choices([0, 1], weights = [prob, 100 - prob], k = 1)[0])
	return sum(violations)

def execute_group(b):
	f = ''.join([f"{name(x)[:-2]}_{vcpus(x)}-" for x in b])[:-1] + '.txt'
	if f not in os.listdir(f"{results_dir}{len(b)}ads/"):
		command = f"/home/ypap/delphi/executions/new_exec.sh" + ''.join([f" {name(x)[:-2]} {vcpus(x)}" for x in b])
		os.system(command)
	total_measures = parse_files(f"{results_dir}{len(b)}ads/")
	print(''.join([f"{b[i]}{' ' * (27 - len(b[i]))}{total_measures[f]['vm_mean_perf'][i]:.2f} | " for i in range(len(b))]))
	return sum([int(total_measures[f]['vm_mean_perf'][i] > slo(b[i])) for i in range(len(b))])

def violations_counter(bins, cl, preds, simulation):
	predictions = dict()
	for f in features:
		with open(get_model(f, cl, 1.2), mode = 'r') as pred_f:
			predictions[f] = dict((rows[0], rows[2]) for rows in csv.reader(pred_f, delimiter='\t') if rows[0] != 'Bench' and rows[0] != 'Accuracy')
	preds_tuple = dict((x, (int(predictions['sens'][x]), int(predictions['cont'][x]))) for x in predictions['sens'].keys())
	results = group_results(3, preds_tuple)
	(violations, triplets) = (0, 0)
	for b in bins:
		if len(b) == 1:
			p = (preds[b[0]]['sens'], sum(preds[b[0]]['cont'].values()))
		#	print(f"{p} {b[0]}{' ' * (27 - len(b[0]))}running alone")
		if len(b) == 2:
			p0 = (preds[b[0]]['sens'], sum(preds[b[0]]['cont'].values()))
			p1 = (preds[b[1]]['sens'], sum(preds[b[1]]['cont'].values()))
			violations += int(heatmap[name(b[0])][name(b[1])] > slo(b[0])) + int(heatmap[name(b[1])][name(b[0])] > slo(b[1]))
		#	print(f"{p0} {b[0]}{' '*(27 - len(b[0]))}{p1} {b[1]}{' ' * (27 - len(b[1]))}{heatmap[name(b[0])][name(b[1])]:.2f} - {heatmap[name(b[1])][name(b[0])]:.2f}  {violations}")
		if len(b) >= 3:
			triplets += 1
			#print(''.join([f"{(preds[x]['sens'], sum(preds[x]['cont'].values()))} {x}{' ' * (27 - len(x))}" for x in b]))
			if simulation: violations += probabilities(list(map(name, b)), cl, preds_tuple, results)
			else: violations += execute_group(b)
	return (bins, violations, triplets)

def slowdown(benchmarks, heatmap):
	# Pythia implementation here
	return list(map(lambda x: (x, float(x.split(',')[-1]) - sum([heatmap[x][y] for y in set(benchmarks).difference([x])])), benchmarks))

def tuples(benchmarks, preds):
	return list(map(lambda x: (x, (preds[x]['sens'], sum([preds[y]['cont'][preds[x]['slo']] for y in set(benchmarks).difference([x])]))), benchmarks))
def ctuples(benchmarks, preds):
	return list(map(lambda x: (x, (preds[x]['sens'], sum(preds[x]['cont'].values()))), benchmarks))

def vcpus(benchmark): return int(benchmark.split(',')[1][-1])
def name(b): return b.split(',')[1]
def slo(b): return float(b.split(',')[-1])
def setting_str(algorithm, version, cl, mode): return f"{algorithm}_{version}_{cl}_{mode}"

sens_factor = 2
def cs_sum(b):
	def s_sum(b): return sens_factor * sum([y[1][0] for y in b])
	def c_sum(b): return sum([y[1][1] for y in b])
	return (s_sum(b), c_sum(b))

def find_fitting_bins(benchmark, bins, alg, preds, cl, mode):
	vcpus_fit = list(filter(lambda x: vcpus(benchmark) + sum(map(vcpus, x)) <= MAX_VCPUS, bins))
	if vcpus_fit == []: bins.append([benchmark])
	else:
		if alg == 'oracle':
			sd_bins = [slowdown(b + [benchmark], preds) for b in vcpus_fit]
			best_fit = list(filter(lambda x: all([y[1] > 0 for y in x]), sd_bins))
			if best_fit == []: bins.append([benchmark])
			else:
				best_bin = min(best_fit, key = lambda x: min([y[1] for y in x]))
				bins[bins.index([x[0] for x in best_bin if x[0] != benchmark])].append(benchmark)
		if alg == 'delphi':
			if mode == 'r':
				t_bins = [tuples(b + [benchmark], preds) for b in vcpus_fit]
				best_fit = list(filter(lambda x: all([0 in y[1] for y in x]), t_bins))
				if best_fit == []: bins.append([benchmark])
				else:
					sum_filter = list(filter(lambda x: (cl == 2 and len(x) == 2) or all([y < len(x) + cl - 2 for y in cs_sum(x)]), best_fit))
					if sum_filter == []: bins.append([benchmark])
					else:
						min_length = min(len(b) for b in sum_filter)
						min_len = list(filter(lambda x: len(x) == min_length, sum_filter))
						best_bin = max(min_len, key = lambda x: sum(cs_sum(x)))
						bins[bins.index([x[0] for x in best_bin if x[0] != benchmark])].append(benchmark)
			if mode == 'c':
				t_bins = [ctuples(b + [benchmark], preds) for b in vcpus_fit]
				best_fit = list(filter(lambda x: list(map(lambda y: y[1], x)).count((0, 0)) >= len(x) - 1, t_bins))
				if best_fit == []: bins.append([benchmark])
				else:
					min_length = min(len(b) for b in best_fit)
					min_len = list(filter(lambda x: len(x) == min_length, best_fit))
					best_bin = max(min_len, key = lambda x: sum(cs_sum(x)))
					bins[bins.index([x[0] for x in best_bin if x[0] != benchmark])].append(benchmark)
		if alg == 'random':			
			bins[bins.index(max(vcpus_fit, key = lambda x: sum(map(vcpus,x))))].append(benchmark)

def best_fit_bin_packing(benchmarks, alg, version, cl, mode):
	benchmarks = sorted(benchmarks, key = vcpus, reverse = True)
	preds = []
	if alg == 'oracle':
		preds = get_heatmap(benchmarks, version)
		benchmarks = sorted(benchmarks, key = lambda x: np.mean(list(preds[x].values())), reverse = True)
	elif alg == 'delphi':
		preds = get_predictions(benchmarks, version, cl)
		benchmarks = sorted(benchmarks, key = lambda x: (preds[x]['sens'], sum(preds[x]['cont'].values())), reverse = True)
	bins = []
	for (i, benchmark) in enumerate(benchmarks): find_fitting_bins(benchmark, bins, alg, preds, cl, mode)
	return bins

alg_config = {'random': [['r'], [2], ['c']],
			  'oracle': [['r', 'p'], [2], ['c']],
			  'delphi': [['r', 'p', 'a'], [2, 3], ['c', 'r']]}

def calculate_bins(args):
	arg_check_binpacking(args)
	algorithms_to_run = alg_config if args[1] == 'all' else args[1].split(',')
	#times_to_run = int(args[2])
	#contentions_to_run = args[3].split(',') if len(args) >= 4 else contentions
	#qos_ins = list(map(float, filter(lambda x: '.' in x, args[4].split(',')))) + \
	#		  list(filter(lambda x: 'all' in x, args[4].split(','))) if len(args) >= 5 else all_slos
	times_to_run = 1
	contentions_to_run = ['l']
	qos_ins = [1.2]
	simulation = args[2] == 's'
	results = dict((qos, dict()) for qos in qos_ins)

	size = 100
	for i in range(times_to_run):
		for (contention, qos_in) in list(product(*[contentions_to_run, qos_ins])):
			#benchmarks = generate_workload(contention, size, qos_in, classes_workload, printed = times_to_run == 1)
			with open(workload_filename(contention, size, qos_in), 'r') as workload_fd:
				bench_list = [row for row in csv.reader(workload_fd)]
			benchmarks = list(set([f"{i},{row[0]},{row[1]}" for (i, row) in enumerate(bench_list)]))
			for algo in algorithms_to_run:
				configs = list(product(*alg_config[algo]))
				for (version, cl, mode) in configs:
					if version == 'a' and cl == 3: continue
					(bins, violations, t) = violations_counter(best_fit_bin_packing(benchmarks, algo, version, cl, mode), cl, get_predictions(benchmarks, 'r', cl), simulation)
					print(f"{algo}{' ' * (10 - len(algo))}{version} | {cl} | {mode}: Bins = {len(bins)} with {violations} violations and {t} triplets")
					set_str = setting_str(algo, version, cl, mode)
					if set_str in results[qos_in]: results[qos_in][set_str].append((len(bins), violations))
					else: results[qos_in][set_str] = [(len(bins), violations)]
	for qos in results:
		try: new_file = os.stat(f"{violations_dir}boxplot-{qos}.csv").st_size == 0
		except: new_file = True
		with open(f"{violations_dir}boxplot-{qos}.csv", 'a', newline='') as csvfile:
			writer = csv.writer(csvfile)
			if new_file: writer.writerow(['algo', 'bins', 'violations'])
			for x in results[qos]:
				name = x if not x.startswith('delphi_a') else 'attackers_r'
				writer.writerow([name, results[qos][x][0][0], results[qos][x][0][1]])

def arg_check_binpacking(args):
	if (len(args) < 3) or \
	   not all(map(lambda x: x in list(alg_config.keys()) + ['all'], args[1].split(','))) or \
	   (len(args) >= 3 and not args[2] in ['s', 'r']):
		print(f"Usage:      {args[0]} <algorithm> <simulation>\n" + \
			  f"Algorithms: {' | '.join(list(alg_config.keys()) + ['all'])}\n" + \
			  f"Simulation: {' | '.join(['s', 'r'])}")
		sys.exit(0)

if __name__ == '__main__':
	calculate_bins(sys.argv)
