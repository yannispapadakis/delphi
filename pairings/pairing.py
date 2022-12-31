#!/usr/bin/python3
from generate_workloads import *
#from attackers_read import attacker_classifier

from matching.algorithms import stable_roommates
import warnings
from matching import Player

report = ''
heatmap = spawn_heatmap()
read_heatmap(heatmap)

"""--------------------------- Random Pairing -----------------------------"""
def random_pairs(benchmarks, version, class_):
	benchmarks = list(map(name_fix, benchmarks))
	while 1:
		try:
			(pairs, paired_ids) = ([], [])
			for bench1 in benchmarks:
				if bench1[0] in paired_ids: continue
				valids = list(filter(lambda x: x[0] not in paired_ids and x[0] != bench1[0], benchmarks))
				bench2 = random.choice(valids)
				pairs.append([bench1, bench2])
				paired_ids.extend([bench1[0], bench2[0]])
			return pairs
		except IndexError:
			continue

"""------------------ Stable Roommates based Algorithms -------------------"""
def oracle(benchmarks, version, class_):
	players = [Player(x) for x in benchmarks]

	window = dict()
	warnings.filterwarnings("ignore", category=UserWarning, module="matching")
	if version == 'r': use_heatmap = heatmap
	else:
		use_heatmap = spawn_heatmap()
		read_heatmap(use_heatmap, 'pred_heatmap')
	for bench1 in players:
		window[bench1] = dict()
		clos = float(bench1.name.split(',')[2])
		for bench2 in set(players).difference([bench1]):
			try: window[bench1][bench2] = use_heatmap[bench1.name.split(',')[1]][bench2.name.split(',')[1]]
			except: window[bench1][bench2] = 0
		bench1.prefs =  list(map(lambda x: x[0],
						sorted(filter(lambda x: float(x[1]) < clos, window[bench1].items()),
						reverse = True, key = itemgetter(1))))
		bench1.prefs += list(map(lambda x: x[0],
						sorted(filter(lambda x: float(x[1]) >= clos, window[bench1].items()),
						key = itemgetter(1))))
	return players_to_str(stable_roommates(players))

def whisker(benchmarks, version, class_):
	players = [Player(x) for x in benchmarks]

	f = open(f"{heatmap_dir}whisker-stats.csv", 'r')
	whisk_str = dict((rows[0], (float(rows[1]), float(rows[2]))) for rows in csv.reader(f))
	f.close()
	whiskers = dict((x, whisk_str[x.name.split(',')[1]]) for x in players)

	for bench in players:
		clos = float(bench.name.split(',')[2])
		if whiskers[bench][0] < clos:
			bench.prefs = list(map(lambda x: x[0],
							sorted(filter(lambda x: x[0] != bench, whiskers.items()),
							reverse = True, key = lambda x: x[1][1])))
		else:
			bench.prefs = list(map(lambda x: x[0],
							sorted(filter(lambda x: x[1][1] < clos and x[0] != bench, whiskers.items()),
							reverse = True, key = lambda x: x[1][1])))
			bench.prefs += list(map(lambda x: x[0],
							sorted(filter(lambda x: x[1][1] >= clos and x[0] != bench, whiskers.items()),
							key = lambda x: x[1][1])))
	return players_to_str(stable_roommates(players))

def players_to_str(holds):
	try: holds = dict((name_fix(x.name), name_fix(holds[x].name)) for x in holds)
	except AttributeError: return -1
	pairs = []
	for bench1 in holds:
		bench2 = holds[bench1]
		if bench2 in [x[0] for x in pairs]: continue
		pairs.append([bench1, bench2])
	return pairs

"""---------------------- delphi Pairing Algorithm ------------------------"""
def get_model(feature, classes, qos):
	run = "spt_cv"
	accuracy = dict()
	for model in chosen_models:
		try: model_pred = open(f"{predictions_dir}{model}/{model}_{feature}_{classes}_{qos}_{run}.csv", 'r')
		except: continue
		predictions = [int(line[1] == line[2]) for line in csv.reader(model_pred, delimiter='\t') if line[0] != 'Bench' and line[0] != 'Accuracy']
		accuracy[model] = sum(predictions) / float(len(predictions))
		model_pred.close()
	model = max(accuracy.items(), key = itemgetter(1))[0]
	#print(f"get_model called with: {feature} {classes} {qos} => {model}")
	#global report
	#if f"{feature} ({qos}): {model} | " not in report: report += f"{feature} ({qos}): {model} | "
	#report = f"{feature} {qos} {classes} | {report}"
	return f"{predictions_dir}{model}/{model}_{feature}_{classes}_{qos}_{run}.csv"

def delphi(benchmarks, version, classes):
	def pair_together(list_to_pair, n, list2):
		pairs = []
		while n < len(list2) and len(list_to_pair) > 1:
			b1, b2 = list_to_pair[:2]
			list_to_pair = list_to_pair[2:]
			list2 = list(set(list2).difference([b1, b2]))
			pairs.append((b1, b2))
		return (pairs, list2)

	def safe_pairs(quiets, not_quiets):
		quiets1 = quiets[:len(not_quiets)]
		quiets2 = quiets[len(not_quiets):]
		return list(zip(quiets1, not_quiets)) + list(zip(quiets2[:int(len(quiets2) / 2)], quiets2[int(len(quiets2) / 2):]))

	def get_predictions(benchmarks, version, classes):
		predictions = dict()
		qos = min(map(lambda x: float(x.split(',')[2]), benchmarks))
		for f in features:
			with open(get_model(f, classes, qos), mode='r') as pred:
				predictions[f] = dict((rows[0], rows[1 + int(version == 'r')]) for rows in csv.reader(pred, delimiter='\t') if rows[0] != 'Bench' and rows[0] != 'Accuracy')
				pred.close()
		return dict((x, (int(predictions['sens'][x.split(',')[1]]), int(predictions['cont'][x.split(',')[1]]))) for x in benchmarks)

	def get_attacker(benchmarks):
		classes = attacker_classifier()
		return dict((x, classes[x.split(',')[1]]) for x in benchmarks)

	preds = get_attacker(benchmarks) if version == 'a' else get_predictions(benchmarks, version, classes)
	zeros = list(filter(lambda x: sum(x[1]) == 0, preds.items()))
	random.shuffle(zeros)
	notzeros = list(set(preds.items()).difference(zeros))
	order = [(1,0), (0,1), (2,0), (0,2), (2,2), (2,1), (1,2), (1,1)]
	pairs = []
	if len(zeros) < len(notzeros):
		for comb in order:
			removing = list(filter(lambda x: x[1] == comb, notzeros))
			random.shuffle(removing)
			(new_pairs, notzeros) = pair_together(removing, len(zeros), notzeros)
			pairs += new_pairs
			if len(zeros) >= len(notzeros):
				break
	pairs += safe_pairs(zeros, notzeros)
	return list(map(lambda x: [name_fix(x[0][0]), name_fix(x[1][0])], pairs))

"""---------------------- delphi3 Pairing Algorithm - mult SLOs -----------"""
def delphi3(benchmarks, version, classes):
	def bad_pairing(combinations, not_quiets, num_quiets, qos):
		pairs = []
		for combination in combinations:
			apps_to_remove = list(filter(lambda x: x[1] == combination, not_quiets))
			while len(apps_to_remove) > 1:
				random.shuffle(apps_to_remove)
				(pair_1, pair_2) = (apps_to_remove.pop(0), apps_to_remove.pop(0))
				not_quiets.remove(pair_1)
				not_quiets.remove(pair_2)
				pairs.append((pair_1[0], pair_2[0]))
				if len(not_quiets) <= num_quiets: return pairs
		return pairs

	def safe_pairs(quiets, not_quiets):
		quiets1 = list(map(lambda x: x[0], quiets[:len(not_quiets)]))
		quiets2 = list(map(lambda x: x[0], quiets[len(not_quiets):]))
		not_quiets = list(map(lambda x: x[0], not_quiets))
		return list(zip(quiets1, not_quiets)) + list(zip(quiets2[:int(len(quiets2) / 2)], quiets2[int(len(quiets2) / 2):]))

	predictions = get_predictions(benchmarks, version, classes)
	slos = sorted(set(map(lambda x: x['slo'], predictions.values())))
	order = [(1,0), (0,1), (2,0), (0,2), (2,2), (2,1), (1,2), (1,1)]
	(not_quiets, pairs) = ([],[])
	for (i, qos) in enumerate(slos):
		quiets = list(filter(lambda x: not any([x[0] in y for y in pairs]),
				 list(map(lambda y: (y[0], (y[1]['sens'], y[1]['cont'][qos])), filter(lambda x: x[1]['sens'] + x[1]['cont'][qos] == 0, list(predictions.items()))))))
		not_quiets = list(filter(lambda x: not any([x[0] in y for y in pairs]),
					 list(map(lambda y: (y[0], (y[1]['sens'], y[1]['cont'][qos])), filter(lambda x: x[1]['sens'] + x[1]['cont'][qos] > 0, list(predictions.items()))))))

		if len(quiets) < len(not_quiets):
			pairs += bad_pairing(order if i + 1 == len(slos) else order[:4], not_quiets, len(quiets), qos)
	pairs += safe_pairs(quiets, not_quiets)
	return list(map(lambda x: map(name_fix, x), pairs))

"""---------------------- delphi Pairing Algorithm - mult SLOs ------------"""
def get_predictions(benchmarks, version, classes):
	predictions = dict()
	slos = sorted(list(set(map(float, map(lambda x: x.split(',')[2], benchmarks)))))
	for s in slos:
		predictions[s] = dict()
		for f in features:
			pred_f = open(get_model(f, classes, s), mode = 'r')
			predictions[s][f] = dict((rows[0], int(rows[1 + int(version == 'r')])) for rows in csv.reader(pred_f, delimiter='\t') if rows[0] != 'Bench' and rows[0] != 'Accuracy')
			pred_f.close()
	return dict((f"{i},{name},{slo}", 
				{'slo': float(slo),
				 'sens': predictions[float(slo)]['sens'][name],
				 'cont': dict((i, predictions[i]['cont'][name]) for i in slos)}) \
				for (i, name, slo) in map(lambda x: x.split(','), benchmarks))

def delphi_2(benchmarks, version, classes):
	def exhaustive_matrix(preds):
		benchmarks = list(preds.keys())
		for row in preds:
			preds[row]['heatmap'] = dict()
			for col in set(benchmarks).difference([row]):
				deny = int(bool(preds[row]['sens'] and preds[col]['cont'][preds[row]['slo']])) or \
					   int(bool(preds[col]['sens'] and preds[row]['cont'][preds[col]['slo']]))
				preds[row]['heatmap'][col] = ((preds[row]['sens'], preds[col]['cont'][preds[row]['slo']]), deny)

	def sort_benchmarks(preds):
		return sorted(sorted(sorted(sorted(list(preds.items()),
			key = lambda x: x[1]['slo'], reverse = True),
			key = lambda x: sum(x[1]['cont'].values()), reverse = True),
			key = lambda x: x[1]['sens'], reverse = True),
			key = lambda x: sum(map(lambda y: y[1], x[1]['heatmap'].values())), reverse = True)

	def wont_find_candidate(queue):
		total_cand_list = []
		for (i, bench) in enumerate(queue):
			candidate_list = list(map(lambda x:x[0], filter(lambda y: y[1][1] == 0, bench[1]['heatmap'].items())))
			total_cand_list = list(set(total_cand_list + candidate_list).difference([bench[0]]))
			#if len(total_cand_list) == (i + 1): print(f"{i+1} : {len(total_cand_list)} | {bench[0].split(',')[0]}: {len(candidate_list)} | {list(map(lambda x: int(x.split(',')[0]), candidate_list))}")
			if len(total_cand_list) < (i + 1): return i
		return -1

	def bad_pairing(queue):
		pairs = []
		error_index = wont_find_candidate(queue)
		while error_index > -1:
			#error_bench = queue.pop(error_index)
			error_bench = queue.pop(0)
			bench_to_pair = queue.pop(0)
			#print(f"BENCH: {error_bench[0]} (idx: {error_index}) will be badly paired with: {bench_to_pair[0]}\n{'-'*50}")
			pairs.append((error_bench[0], bench_to_pair[0]))
			error_index = wont_find_candidate(queue)
		return (pairs, queue)

	preds = get_predictions(benchmarks, version, classes)
	exhaustive_matrix(preds)
	queue = sort_benchmarks(preds)
	#for x in queue: print(f"{x[0]}{' '*(25 - len(x[0]))}{x[1]['slo']}{' '*4}{x[1]['sens']}{' '*4}{x[1]['cont']}{' '*4}{sum(map(lambda y: y[1], x[1]['heatmap'].values()))} {len(x[1]['heatmap'])}")
	pairs = []
	(pairs, queue) = bad_pairing(queue)
	scrap = []
	while queue:
		bench = queue.pop(0)
		candidates = list(filter(lambda y: y[1][1] == 0 and y[0] in map(lambda x: x[0], queue), bench[1]['heatmap'].items()))
		if len(candidates) == 0:
			print(f"No candidates for {bench[0]}")
			scrap.append(bench)
		else:
			sens_combination = max(set(map(lambda x: x[1][0], candidates)), key = lambda y: sum(y))
			sens_candidates = list(map(lambda z: z[0], filter(lambda y: y[1][0] == sens_combination, candidates)))
			cont_combination = max([preds[cand]['heatmap'][bench[0]][0] for cand in sens_candidates])
			cont_candidates = list(filter(lambda x: preds[x]['heatmap'][bench[0]][0] == cont_combination, sens_candidates))
			pred_candidates = dict((x[0], x[1]) for x in filter(lambda x: x[0] in cont_candidates, preds.items()))
			sub_queue = sort_benchmarks(pred_candidates)
			pair = queue.pop(queue.index(sub_queue[0]))
			pairs.append((bench[0], pair[0]))
	return list(map(lambda x: map(name_fix, x), pairs))

"""------------------------- Helper Functions -----------------------------"""
def violations_counter(pairs):
	violations = 0
	if type(pairs) != list: return -1
	for (bench1, bench2) in pairs:
		(name1, name2) = (bench1[1], bench2[1])
		try: sd1 = heatmap[name1][name2]
		except KeyError: sd1 = 0
		try: sd2 = heatmap[name2][name1]
		except KeyError: sd2 = 0
		violations += int(sd1 > bench1[2]) + int(sd2 > bench2[2])
	return violations
	
def name_fix(name):
	tokens = name.split(',')
	return (int(tokens[0]), tokens[1], float(tokens[2]))

"""------------------------------- Main -----------------------------------"""
alg_config = {'random':  [random_pairs,	100, ['r'],      [2]],
			  'oracle':  [oracle,		1,   ['r', 'p'], [2]],
			  'whisker': [whisker,		1,   ['r'],      [2]],
#			  'delphi':  [delphi,		100, ['r', 'p'], [2, 3]],
#			  'delphi2': [delphi_2,		1,   ['r', 'p'], [2, 3]],
			  'delphi3': [delphi3,		100, ['r', 'p'], [2, 3]]}

def run_all_algorithms(args):
	arg_check_pairing(args)
	algorithms_to_run = alg_config if args[1] == 'all' else args[1].split(',')
	if all([x.isdigit() for x in args[2]]):
		times_to_run = int(args[2])
		contentions_to_run = contentions
		qos_ins = [1.1, 1.2, 'all']
	else:
		times_to_run = 1
		contentions_to_run = args[2].split(',')
		qos_ins = list(map(float, filter(lambda x: '.' in x, args[3].split(',')))) + \
				  list(filter(lambda x: 'all' in x, args[3].split(',')))
	size = 100
	classes_workload = 2
	results = dict()
	for i in range(times_to_run):
		for (contention, qos_in) in list(product(*[contentions_to_run, qos_ins])):
			benchmarks = generate_workload(contention, size, qos_in, classes_workload, printed = times_to_run == 1)
			workload = workload_filename(contention, size, qos_in)
			print(f"{'-'*40} {workload.split('/')[-1]} {'-'*(50 - len(workload.split('/')[-1]))}")
			for algo in algorithms_to_run:
				(runs, versions, classes) = alg_config[algo][1:]
				configs = list(product(*[versions, classes]))
				for (version, cl) in configs:
					tries = 10
					while tries > 0:
						violations = np.mean([violations_counter(alg_config[algo][0](benchmarks, version, cl)) for i in range(runs)])
						if violations == -1:
							tries -= 1
						else: break
					conf_str = f" {version} - {cl}" if len(configs) > 1 else ""
					print(f"{algo}{conf_str}: {violations}")
					if violations > -1:
						if (contention, qos_in, algo, version, cl) in results: results[(contention, qos_in, algo, version, cl)].append(violations)
						else: results[(contention, qos_in, algo, version, cl)] = [violations]
	for configuration in results: results[configuration] = np.mean(results[configuration])
	pprint.pprint(results)

def arg_check_pairing(args):
	if (len(args) < 3) or \
	   not all(map(lambda x: x in list(alg_config.keys()) + ['all'], args[1].split(','))) or \
	   (len(args) == 3 and not all([x.isdigit() for x in args[2]])) or \
	   (len(args) == 4 and not all(map(lambda x: x in contentions, args[2].split(',')))) or \
	   (len(args) == 4 and not all(map(lambda x: x in list(map(str, qos_levels)) + ['all'], args[3].split(',')))):
		print(f"Usage:      {args[0]} <algorithm> <contention | times to run> <qos>\n" + \
			  f"Algorithms: {' | '.join(list(alg_config.keys()) + ['all'])}\n" + \
			  f"Contention: {' | '.join(contentions)}\n" + \
			  f"QoS incl.:  {' | '.join(list(map(str, qos_levels)) + ['all'])}")
		sys.exit(0)

if __name__ == '__main__':
	run_all_algorithms(sys.argv)
