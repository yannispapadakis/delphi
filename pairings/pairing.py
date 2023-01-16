#!/usr/bin/python3
from generate_workloads import *
#from attackers_read import attacker_classifier

from alive_progress import alive_bar
from matching.algorithms import stable_roommates
import warnings
import pickle
from matching import Player

report = ''
contention_now = 'l'
probabilities = {c: {} for c in [2, 3]}
size = 100
classes_workload = 2
all_slos = [1.1, 1.2, 'all']
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
	def players_to_str(holds):
		try: holds = dict((name_fix(x.name), name_fix(holds[x].name)) for x in holds)
		except AttributeError: return -1
		pairs = []
		for bench1 in holds:
			bench2 = holds[bench1]
			if bench2 in [x[0] for x in pairs]: continue
			pairs.append([bench1, bench2])
		return pairs

	players = [Player(x) for x in benchmarks]

	window = dict()
	warnings.filterwarnings("ignore", category=UserWarning, module="matching")
	if version == 'r': use_heatmap = heatmap
	else:
		use_heatmap = spawn_heatmap()
		read_heatmap(use_heatmap, 'pred_heatmap')

	rejected = [1]
	total_rejected = []
	while len(rejected) % 2:
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
		holds = stable_roommates(players)

		rejected = list(filter(lambda x: not holds[x], holds.keys()))
		if not rejected: break
		if len(rejected) % 2:
			big_cycle = list(filter(lambda x: holds[x] and holds[holds[x]] != x, holds.keys()))
			rejected.append(big_cycle[0])
		total_rejected.extend(rejected)
		players = [x for x in players if x not in rejected]

	bad_pairs = [(total_rejected[i], total_rejected[i + 1]) for i in range(0, len(total_rejected), 2)]
	for (x, y) in bad_pairs:
		holds[x] = y
		del holds[y]
	return players_to_str(holds)

"""---------------------- delphi Pairing Algorithm ------------------------"""
def get_model(feature, classes, qos):
	run = "spt_cv"
	accuracy = dict()
	for model in chosen_models:
		with open(f"{predictions_dir}{model}/{model}_{feature}_{classes}_{qos}_{run}.csv", 'r') as model_pred:
			predictions = [int(line[1] == line[2]) for line in csv.reader(model_pred, delimiter='\t') if line[0] != 'Bench' and line[0] != 'Accuracy']
			accuracy[model] = sum(predictions) / float(len(predictions))
	model = max(accuracy.items(), key = itemgetter(1))[0]
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
def get_predictions(benchmarks, version, classes):
	predictions = dict()
	slos = sorted(list(set(map(float, map(lambda x: x.split(',')[2], benchmarks)))))
	for s in slos:
		predictions[s] = dict()
		for f in features:
			with open(get_model(f, classes, s), mode = 'r') as pred_f:
				predictions[s][f] = dict((rows[0], int(rows[1 + int(version == 'r')])) for rows in csv.reader(pred_f, delimiter='\t') if rows[0] != 'Bench' and rows[0] != 'Accuracy')
	return dict((f"{i},{name},{slo}",
				{'slo': float(slo),
				 'sens': predictions[float(slo)]['sens'][name],
				 'cont': dict((i, predictions[i]['cont'][name]) for i in slos)}) \
				for (i, name, slo) in map(lambda x: x.split(','), benchmarks))

def delphi3(benchmarks, version, classes):
	def bad_pairing(not_quiets, num_quiets, qos):
		def draw_app(probability, not_quiets, class1):
			available_classes = list(set([app[1] for app in not_quiets]))
			if class1: prob = [probability[class1][x] for x in available_classes]
			else: prob = [1 - probability[x][(0, 0)] for x in available_classes]
			picked_class = random.choices(available_classes, prob)[0]
			apps_at_class = list(filter(lambda x: x[1] == picked_class, not_quiets))
			return random.choice(apps_at_class)

		pairs = []
		probability = probabilities[classes][contention_now]
		while len(not_quiets) > num_quiets:
			pair1 = draw_app(probability, not_quiets, None)
			not_quiets.remove(pair1)
			pair2 = draw_app(probability, not_quiets, pair1[1])
			not_quiets.remove(pair2)
			pairs.append((pair1[0], pair2[0]))
		return pairs

	def safe_pairs(quiets, not_quiets):
		quiets1 = list(map(lambda x: x[0], quiets[:len(not_quiets)]))
		quiets2 = list(map(lambda x: x[0], quiets[len(not_quiets):]))
		not_quiets = list(map(lambda x: x[0], not_quiets))
		return list(zip(quiets1, not_quiets)) + list(zip(quiets2[:int(len(quiets2) / 2)], quiets2[int(len(quiets2) / 2):]))

	predictions = get_predictions(benchmarks, version, classes)
	slos = sorted(set(map(lambda x: x['slo'], predictions.values())))
	(not_quiets, pairs) = ([],[])
	for (i, qos) in enumerate(slos):
		quiets = list(filter(lambda x: not any([x[0] in y for y in pairs]),
				 list(map(lambda y: (y[0], (y[1]['sens'], y[1]['cont'][qos])), filter(lambda x: x[1]['sens'] + x[1]['cont'][qos] == 0, list(predictions.items()))))))
		not_quiets = list(filter(lambda x: not any([x[0] in y for y in pairs]),
					 list(map(lambda y: (y[0], (y[1]['sens'], y[1]['cont'][qos])), filter(lambda x: x[1]['sens'] + x[1]['cont'][qos] > 0, list(predictions.items()))))))

		if len(quiets) < len(not_quiets):
			pairs += bad_pairing(not_quiets, len(quiets), qos)
	pairs += safe_pairs(quiets, not_quiets)
	return list(map(lambda x: tuple(map(name_fix, x)), pairs))

"""------------------------- Helper Functions -----------------------------"""
alg_config = {'random':	[random_pairs,	100, ['r'],      [2]],
			  'oracle':	[oracle,		1,   ['r', 'p'], [2]],
			  'delphi':	[delphi3,		100, ['r', 'p'], [2, 3]]}

def violations_counter(pairs):
	violations = 0
	for (bench1, bench2) in pairs:
		(name1, name2) = (bench1[1], bench2[1])
		try: sd1 = heatmap[name1][name2]
		except KeyError: sd1 = 0
		try: sd2 = heatmap[name2][name1]
		except KeyError: sd2 = 0
		violations += int(sd1 > bench1[2]) + int(sd2 > bench2[2])
	return violations
	
def calculate_probabilities(pairings, cl):
	combinations = list(product(range(cl), repeat=2))
	paired = {combination: {combination: 0 for combination in combinations} for combination in combinations}
	for pairs in pairings:
		predictions = get_predictions([tuple_fix(x) for pair in pairs for x in pair], 'r', cl)
		for (bench1, bench2) in pairs:
			(b1, b2) = (tuple_fix(bench1), tuple_fix(bench2))
			class_of_bench1 = (predictions[b1]['sens'], predictions[b1]['cont'][predictions[b2]['slo']])
			class_of_bench2 = (predictions[b2]['sens'], predictions[b2]['cont'][predictions[b1]['slo']])
			paired[class_of_bench1][class_of_bench2] += 1

	pairs_per_class = dict()
	probability = {combination: {combination: 0 for combination in combinations} for combination in combinations[1:]}
	for (i, class1) in enumerate(combinations[1:]):
		other_pairs = [paired[x][class1] for x in paired if x != class1 and x != (0, 0)]
		pairs_per_class[class1] = sum([paired[class1][x] for x in paired[class1] if x != (0, 0)]) + sum(other_pairs)
		occurences_0 = paired[class1][(0, 0)] + paired[(0, 0)][class1]
		total_occurences = float(pairs_per_class[class1] + occurences_0)
		probability[class1][(0, 0)] = occurences_0 / total_occurences if total_occurences > 0 else 0.0
		for (j, class2) in enumerate(combinations[1:]):
			probability[class1][class2] = (paired[class1][class2] + paired[class2][class1] * int(i != j)) / float(pairs_per_class[class1]) if pairs_per_class[class1] > 0 else 0
	return probability

def get_probabilities_oracle(contentions_to_run):
	times_to_run = 1000

	with alive_bar(len(alg_config['delphi'][3]) * len(contentions_to_run) * times_to_run) as bar:
		for c in alg_config['delphi'][3]:
			for contention in contentions_to_run:
				pairings = []
				for i in range(1000):
					for qos_in in all_slos:
						benchmarks = generate_workload(contention, size, qos_in, classes_workload, printed = False)
						pairings.append(oracle(benchmarks, 'r', c))
					bar()
				probabilities[c][contention] = calculate_probabilities(pairings, c)

def setting_str(contention, algorithm, version, cl): return f"{contention}_{algorithm}_{version}_{cl}"
def tuple_fix(b): return f"{b[0]},{b[1]},{b[2]}"

def name_fix(name):
	tokens = name.split(',')
	return (int(tokens[0]), tokens[1], float(tokens[2]))

def write_dict_to_file(dictionary, filepath):
	with open(filepath, 'wb') as f: pickle.dump(dictionary, f)

def read_dict_from_file(filepath):
	with open(filepath, 'rb') as f: return pickle.load(f)


"""------------------------------- Main -----------------------------------"""
def run_all_algorithms(args):
	arg_check_pairing(args)
	algorithms_to_run = alg_config if args[1] == 'all' else args[1].split(',')
	times_to_run = int(args[2])
	contentions_to_run = args[3].split(',') if len(args) >= 4 else contentions
	qos_ins = list(map(float, filter(lambda x: '.' in x, args[4].split(',')))) + \
			  list(filter(lambda x: 'all' in x, args[4].split(','))) if len(args) >= 5 else all_slos
	results = dict((qos, dict()) for qos in qos_ins)

	global probabilities
	if 'delphi' in algorithms_to_run:
		try: probabilities = read_dict_from_file(f"{heatmap_dir}probabilities.txt")
		except:
			get_probabilities_oracle(contentions_to_run)
			write_dict_to_file(probabilities, f"{heatmap_dir}probabilities.txt")
	with alive_bar(times_to_run) as bar:
		for i in range(times_to_run):
			for (contention, qos_in) in list(product(*[contentions_to_run, qos_ins])):
				global contention_now
				contention_now = contention
				benchmarks = generate_workload(contention, size, qos_in, classes_workload, printed = times_to_run == 1)
				#with open(workload_filename(contention, size, qos_in), 'r') as workload_fd:
				#	bench_list = [row for row in csv.reader(workload_fd)]
				#benchmarks = list(set([f"{i},{row[0]},{row[1]}" for (i, row) in enumerate(bench_list)]))
				workload = workload_filename(contention, size, qos_in)
				for algo in algorithms_to_run:
					(runs, versions, classes) = alg_config[algo][1:]
					configs = list(product(*[versions, classes]))
					for (version, cl) in configs:
						violations = np.mean([violations_counter(alg_config[algo][0](benchmarks, version, cl)) for i in range(runs)])
						set_str = setting_str(contention, algo, version, cl)
						if set_str in results[qos_in]: results[qos_in][set_str].append(violations)
						else: results[qos_in][set_str] = [violations]
			bar()
	for qos in results:
		resultsT = zip(*[(k, *v) for k, v in results[qos].items()])
		with open(f"{violations_dir}boxplot-{qos}.csv", 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerows(resultsT)

def arg_check_pairing(args):
	if (len(args) < 3) or \
	   not all(map(lambda x: x in list(alg_config.keys()) + ['all'], args[1].split(','))) or \
	   (len(args) >= 3 and not all([x.isdigit() for x in args[2]])) or \
	   (len(args) >= 4 and not all(map(lambda x: x in contentions, args[3].split(',')))) or \
	   (len(args) == 5 and not all(map(lambda x: x in list(map(str, all_slos)), args[4].split(',')))):
		print(f"Usage:      {args[0]} <algorithm> <times to run> <contention> <qos>\n" + \
			  f"Algorithms: {' | '.join(list(alg_config.keys()) + ['all'])}\n" + \
			  f"Contention: {' | '.join(contentions)}\n" + \
			  f"QoS incl.:  {' | '.join(list(map(str, all_slos)))}")
		sys.exit(0)

if __name__ == '__main__':
	run_all_algorithms(sys.argv)
