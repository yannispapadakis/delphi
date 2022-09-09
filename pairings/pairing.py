#!/usr/bin/python3
sys.path.append('../predict/')
from heatmap_reader import *
#from attackers_read import attacker_classifier

from matching.algorithms import stable_roommates
from matching import Player

clos = 1.1
report = ''
grid = generate_grid()
read_grid(grid)

pred_dir = home_dir + 'results/predictions/'
wd_dir = home_dir + 'pairings/workload_pairs/' 

"""--------------------------- Random Pairing -----------------------------"""
def random_pairs(benchmarks):
	benchmarks = list(map(lambda x: (int(x.split('.')[0]), x.split('.')[1]), benchmarks))
	while 1:
		try:
			pairs = []
			paired_ids = []
			for bench1 in benchmarks:
				if bench1[0] in paired_ids: continue
				valids = [bench2 for bench2 in benchmarks if bench2[0] not in paired_ids and bench1[0] != bench2[0]]
				bench2 = random.choice(valids)
				pairs.append([str(bench1[0]) +'.'+ bench1[1], str(bench2[0]) +'.'+ bench2[1]])
				paired_ids.extend([bench1[0], bench2[0]])
			return pairs
		except IndexError:
			continue

"""------------------ Stable Roommates based Algorithms -------------------"""
def oracle(benchmarks, mode = 'real'):
	players = [Player(x) for x in benchmarks]

	window = dict()
	if mode == 'real': use_grid = grid
	elif mode == 'pred':
		use_grid = generate_grid()
		read_grid(use_grid, 'pred_grid')
	for bench1 in players:
		window[bench1] = dict()
		for bench2 in set(players).difference([bench1]):
			try:
				window[bench1][bench2] = use_grid[bench1.name.split('.')[1]][bench2.name.split('.')[1]]
			except:
				window[bench1][bench2] = 0
		bench1.prefs = list(map(lambda x: x[0],
						sorted([x for x in window[bench1].items() if float(x[1]) < clos], reverse = True,
						key = itemgetter(1))))
		bench1.prefs += list(map(lambda x: x[0],
						sorted([x for x in window[bench1].items() if float(x[1]) >= clos],
						key = itemgetter(1))))
	return players_to_str(stable_roommates(players))

def get_whiskers():
	dicts = []
	for feature in ['sens', 'cont']:
		f = open(pred_dir + feature + '-stats.csv', mode = 'r')
		reader = csv.reader(f)
		whiskers = dict((rows[0], rows[-1]) for rows in reader)
		del whiskers['Benchmark']
		dicts.append(whiskers)
		f.close()
	return dicts

def whisker(benchmarks):
	players = [Player(x) for x in benchmarks]

	(sens_whiskers, cont_whiskers) = get_whiskers()
	whiskers = dict((x, (float(sens_whiskers[x.name.split('.')[1]]), float(cont_whiskers[x.name.split('.')[1]]))) for x in players)
	prefs = dict()

	for bench in players:
		if whiskers[bench][0] < clos:
			bench.prefs = list(map(lambda x: x[0],
							sorted([x for x in whiskers.items() if x[0] != bench], reverse = True,
							key = lambda x: x[1][1])))
		else:
			bench.prefs = list(map(lambda x: x[0],
							sorted([x for x in whiskers.items() if x[1][1] < clos and x[0] != bench], reverse = True,
							key = lambda x: x[1][1])))
			bench.prefs += list(map(lambda x: x[0],
							sorted([x for x in whiskers.items() if x[1][1] >= clos and x[0] != bench],
							key = lambda x: x[1][1])))
	return players_to_str(stable_roommates(players))

"""---------------------- Custom Pairing Algorithm ------------------------"""
def pair_together(list_to_pair, n, list2):
	pairs = []
	while n < len(list2) and len(list_to_pair) > 1:
		b1, b2 = list_to_pair[:2]
		list_to_pair = list_to_pair[2:]
		list2 = list(set(list2).difference([b1, b2]))
		pairs.append((b1, b2))
	return (pairs, list2)

def zipthem(zeros, notzeros):
	zeros1 = zeros[:len(notzeros)]
	zeros2 = zeros[len(notzeros):]
	return list(zip(zeros1, notzeros)) + list(zip(zeros2[:int(len(zeros2) / 2)], zeros2[int(len(zeros2) / 2):]))

def get_model(feature, classes, qos = clos):
	accs = dict()
	for model in ['SVC', 'DT', 'KN', 'RF']:
		cmd = 'tail -n1 ' + pred_dir + model + '/' + '_'.join(map(str, [feature, classes, qos, model])) + '.csv'
		last_line = subprocess.check_output(cmd, shell = True)
		accs[model] = float(str(last_line).split('t')[1].split(' ')[0])
	model = max(accs.items(), key = itemgetter(1))[0]
	global report
	report += feature + ': ' + model + ' '
	return pred_dir + model + '/' + '_'.join(map(str, [feature, classes, qos, model])) + '.csv'

def get_predictions(benchmarks, real, classes):
	predictions = dict()
	features = ['sens', 'cont']
	for f in features:
		with open(get_model(f, classes), mode='r') as pred:
			reader = csv.reader(pred, delimiter='\t')
			predictions[f] = dict((rows[0], rows[-1 if real else 1]) for rows in reader)
			del predictions[f]['Bench']
			del predictions[f]['Accuracy']
			pred.close()
	return dict((x, (int(predictions['sens'][x.split('.')[1]]), int(predictions['cont'][x.split('.')[1]]))) for x in benchmarks)

def get_attacker(benchmarks):
	classes = attacker_classifier()
	return dict((x, classes[x.split('.')[1]]) for x in benchmarks)

def custom(benchmarks, real = False, classes = 3, attackers = False):
	if attackers: preds = get_attacker(benchmarks)
	else: preds = get_predictions(benchmarks, real, classes)
	zeros = [x for x in preds.items() if sum(x[1]) == 0]
	random.shuffle(zeros)
	notzeros = [x for x in preds.items() if x not in zeros]
	order = [(1,0), (0,1), (2,0), (0,2), (2,2), (2,1), (1,2), (1,1)]
	pairs = []
	if len(zeros) < len(notzeros):
		for comb in order:
			removing = [x for x in notzeros if x[1] == comb]
			random.shuffle(removing)
			(new_pairs, notzeros) = pair_together(removing, len(zeros), notzeros)
			pairs += new_pairs
			if len(zeros) >= len(notzeros):
				break
	pairs += zipthem(zeros, notzeros)
	return list(map(lambda x: [x[0][0], x[1][0]], pairs))

"""------------------------- Helper Functions -----------------------------"""
def violations_counter(pairs):
	sd = dict()
	for bb1,bb2 in pairs:
		b1 = bb1.split('.')[1]
		b2 = bb2.split('.')[1]
		try:
			sd1 = grid[b1][b2]
		except KeyError:
			sd1 = 0
		try:
			sd2 = grid[b2][b1]
		except:
			sd2 = 0
		sd[bb1+'_'+bb2] = (sd1, sd2)
	violations = 0
	for p in sd:
		m1, m2 = sd[p]
		violations += int(m1 > clos) + int(m2 > clos)
		#print(p.split('_')[0] + ',' + p.split('_')[1] + ',' + str(m1) + ',' + str(m2))
	return violations

def fix_pairing(holds):
	if not holds: return -1
	if type(holds) == dict:
		pairs = []
		if not holds: return -1
		for bench1 in holds:
			bench2 = holds[bench1]
			if bench2 in [x[0] for x in pairs]: continue
			pairs.append([bench1,bench2])
	else: pairs = holds
	violations = violations_counter(pairs)
	pairs = map(lambda x: [x[0].split('.')[1], x[1].split('.')[1]], pairs)
	return violations

def players_to_str(pairs):
	try:
		return dict((x.name, pairs[x].name) for x in pairs)
	except AttributeError:
		return {}

def print_results(results):
	fd = open(csv_dir + 'violations/' + 'violations_' + str(clos) + '.csv', 'w')
	wr = csv.writer(fd, delimiter = ',')
	sizes = list(map(str, sorted(map(int, results.keys()))))
	files = list(results[sizes[0]].keys())[::-1]
	algorithms = results[sizes[0]][files[0]].keys()
	for size in sizes:
		wr.writerow([size] + files)
		for algo in algorithms:
			algo_pr = algo
			if '_' in algo:
				tokens = algo.split('_')
				algo_pr = tokens[0].title() + ' (' + tokens[1].title() + ', ' + tokens[2] + ')'
			row = [algo_pr]
			for f in files:
				row.append(results[size][f][algo])
			wr.writerow(row)
		wr.writerow([])
	fd.close()

def decide_pairs(benchmarks, algo, real = True, classes = 2):
	benchmarks = list(set([str(i) + '.' + x for (i, x) in enumerate(benchmarks)]))
	if algo == 'random':
		pairs = random_pairs(benchmarks)
	elif algo in ['oracle', 'forest']:
		pairs = oracle(benchmarks, 'real' if algo == 'oracle' else 'pred')
	elif algo == 'whisker':
		pairs = whisker(benchmarks)
	elif algo in ['custom', 'attackers']:
		pairs = custom(benchmarks, real, classes, algo == 'attackers')
	return fix_pairing(pairs)
			
def help_message(ex):
	msg =  "Usage for loop:    %s loop <clos>\n" % ex
	msg += "Usage for manual:  %s <clos> <workload> <algorithm> <real> <classes>\n" % ex
	msg += "CLoS:              " + ' | '.join(sorted(set(map(lambda x: x.split('_')[2], os.listdir(pred_dir + 'SVC/'))))) + '\n'
	msg += "Workload:          " + ' | '.join(list(map(lambda x: x.split('.')[0], filter(lambda x: x.endswith('csv'), os.listdir('workload_pairs/'))))) +'\n'
	msg += "Algorithms:        " + ' | '.join(['oracle', 'forest', 'attackers', 'whisker', 'random', 'custom']) +'\n'
	msg += "Real:    (custom)  " + ' | '.join(['real', 'pred']) +'\n'
	msg += "Classes: (custom)  " + ' | '.join(['2','3']) 
	print(msg)
	return 0

"""------------------------------- Main -----------------------------------"""
def manual(args):
	global clos
	clos = float(args[1])
	bench_file = wd_dir + args[2] + '.csv'
	algo = args[3]
	if algo == 'custom':
		try:
			real = args[4] == 'real'
		except:
			real = True
		try:
			classes = int(args[5])
		except:
			classes = 2
	else:
		real = True
		classes = 2
	fd = open(bench_file)
	reader = csv.reader(fd, delimiter=',')
	benchmarks = [row[0] + '-' + row[1] for row in reader]
	if len(benchmarks) % 2:
		benchmarks.append(benchmarks[0])
	pairs = decide_pairs(benchmarks, algo, real, classes)
	fd.close()
	print(report + ' ' + str(pairs))

def loop(args):
	global clos
	clos = float(args[1])
	files = list(filter(lambda x: x.endswith('csv'), os.listdir(wd_dir)))
	workloads = set(map(lambda x: x.split('-')[0], files))
	sizes = set(map(lambda x: x.split('-')[1].split('.')[0], files))
	algorithms = ['oracle', 'whisker', 'random', 'attackers', 'forest',
				  'custom_real_2', 'custom_real_3', 'custom_pred_2', 'custom_pred_3']
	results = OrderedDict()
	for size in sizes:
		print("Size:", size)
		results[size] = OrderedDict()
		for _file in workloads:
			results[size][_file] = OrderedDict()
			print("\tWorkload:", _file)
			bench_file = wd_dir + _file + '-' + size + '.csv'
			bench_f = open(bench_file)
			reader = csv.reader(bench_f, delimiter=',')
			benchmarks = [row[0] + '-' + row[1] for row in reader]

			for algo in algorithms:
				if algo in ['oracle', 'forest', 'whisker']:
					violations = [decide_pairs(benchmarks, algo)]
				elif algo == 'random' or algo == 'attackers':
					violations = []
					for i in range(100):
						violations.append(decide_pairs(benchmarks, algo))
				elif algo.startswith('custom'):
					violations = []
					(algorithm, real, classes) = algo.split('_')
					for i in range(100):
						violations.append(decide_pairs(benchmarks, algorithm, real, int(classes)))
				print("\t\tAlgorithm:", algo, np.mean(violations))
				results[size][_file][algo] = np.mean(violations)
			bench_f.close()
	print_results(results)

if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.exit(help_message(sys.argv[0]))
	if sys.argv[1] == 'loop': loop(sys.argv[1:])
	else: manual(sys.argv)
