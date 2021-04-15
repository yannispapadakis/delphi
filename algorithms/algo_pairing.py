import random, sys, csv, itertools
import numpy as np
from operator import itemgetter
sys.path.append('../perf_runs/')
from read_attackers import attacker_classifier
sys.path.append('../grid_runs/')
from grid import *
from stableroomate import *
import pprint

clos = 1.2
grid = generate_grid()
read_grid(grid)

csv_dir = '/home/ypap/characterization/parse_results/csv/predictions/'
wd_dir = '/home/ypap/characterization/algorithms/workload_pairs/' 

############################## Random Pairing ##############################

def random_pairs(benchmarks):
	while 1:
		try:
			pairs = random_try(benchmarks)
			return pairs
		except IndexError:
			pass

def random_try(benchmarks1):
	benchmarks = []
	for b in benchmarks1:
		i = int(b.split('.')[0])
		bench = b.split('.')[1]
		bench, vcpus = bench.split('-')
		vcpus = int(vcpus)
		benchmarks.append((i, bench, vcpus))
	pairs = []
	paired_ids = []
	for bench1 in benchmarks1:
		i = int(bench1.split('.')[0])
		if i in paired_ids: continue
		valids = [bench2 for bench2 in benchmarks1 if int(bench2.split('.')[0]) not in paired_ids and i != int(bench2.split('.')[0])]
		bench2 = random.choice(valids)
		pairs.append([bench1, bench2])
		paired_ids.extend([i, int(bench2.split('.')[0])])
	return print_sd(pairs)
	return pairs

############################ Roommates based Algorithms ###########################

def oracle(benchmarks, mode = 'real'):
	window = dict()
	prefs = dict()
	if mode == 'real': use_grid = grid
	elif mode == 'pred':
		use_grid = generate_grid()
		read_grid(use_grid, 'pred_grid')
	for bench1 in benchmarks:
		window[bench1] = dict()
		for bench2 in set(benchmarks).difference([bench1]):
			try:
				window[bench1][bench2] = use_grid[bench1.split('.')[1]][bench2.split('.')[1]]
			except:
				window[bench1][bench2] = 0
		prefs[bench1] = map(lambda x: x[0],
						sorted([x for x in window[bench1].items() if float(x[1] < clos)], reverse = True, 
						key = itemgetter(1)))
		prefs[bench1] += map(lambda x: x[0],
						sorted([x for x in window[bench1].items() if float(x[1] > clos)],
						key = itemgetter(1)))
	return prefs

def whisker_based(benchmarks):
	sens_whiskers = make_grid('sens', [clos])[1]
	cont_whiskers = make_grid('cont', [clos])[1]
	whiskers = dict((x, (sens_whiskers[x.split('.')[1]], cont_whiskers[x.split('.')[1]])) for x in benchmarks)
	prefs = dict()
	for bench in benchmarks:
		if whiskers[bench][0] < clos - 0.1:
			prefs[bench] = map(lambda x: x[0],
							sorted([x for x in whiskers.items() if x[0] != bench], reverse = True,
							key = lambda x: x[1][1]))
		else:
			prefs[bench] = map(lambda x: x[0],
							sorted([x for x in whiskers.items() if x[1][1] < clos and x[0] != bench], reverse = True,
							key = lambda x: x[1][1]))
			prefs[bench] += map(lambda x: x[0],
							sorted([x for x in whiskers.items() if x[1][1] >= clos and x[0] != bench],
							key = lambda x: x[1][1]))

#		if whiskers[bench][0] < clos:
#			prefs[bench] = map(lambda x: x[0],
#							sorted([x for x in whiskers.items() if x[1][1] < clos and x[0] != bench], reverse = True,
#							key = lambda x: x[1][1]))
#			prefs[bench] += map(lambda x: x[0],
#							sorted([x for x in whiskers.items() if x[1][1] >= clos and x[0] != bench],
#							key = lambda x: x[1][1]))
#		else:
#			prefs[bench] = map(lambda x: x[0],
#							sorted([x for x in whiskers.items() if x[0] != bench],
#							key = lambda x: x[1][1]))
	return prefs

def predictor_based(benchmarks, real = False):
	predictions = dict()
	features = ['sens', 'cont']
	suffix = '_' + str(clos) + '.csv'
	for f in features:
		with open(csv_dir + f + suffix, mode='r') as pred:
			reader = csv.reader(pred, delimiter='\t')
			predictions[f] = dict((rows[0], rows[3]) for rows in reader) if real else dict((rows[0], rows[2]) for rows in reader)
			del predictions[f]['Bench']
			pred.close()
	preds = dict((x, (float(predictions['sens'][x.split('.')[1]]), float(predictions['cont'][x.split('.')[1]]))) for x in benchmarks)
	prefs = dict()
	for bench in benchmarks:
		if preds[bench][0] < -1:
			prefs[bench] = map(lambda x: x[0],
							sorted([x for x in preds.items() if x[0] != bench],
								reverse = True, key = lambda x: x[1][1]))
		else:
			prefs[bench] = map(lambda x: x[0],
							sorted([x for x in preds.items() if x[1][1] < 0 and x[0] != bench],
									reverse = True, key = lambda x: x[1][1]))
			prefs[bench] += map(lambda x: x[0],
							sorted([x for x in preds.items() if x[1][1] > 0 and x[0] != bench],
									key = lambda x: x[1][1]))
#####Same but start from 0 (clear distinction of classes)
#		if preds[bench][0] < 0:
#			prefs[bench] = map(lambda x: x[0],
#							sorted([x for x in preds.items() if x[1][1] < 0 and x[0] != bench],
#									reverse = True, key = lambda x: x[1][1]))
#			prefs[bench] += map(lambda x: x[0],
#							sorted([x for x in preds.items() if x[1][1] > 0 and x[0] != bench],
#									key = lambda x: x[1][1]))
#		else:			
#			prefs[bench] = map(lambda x: x[0],
#							sorted([x for x in preds.items() if x[0] != bench],
#									key = lambda x: x[1][1]))
#####Sort by Classes and decision function
#		prefs[bench] = map(lambda x: x[0], 
#						sorted([x for x in preds.items() if x[1][1] * preds[bench][0] < 0 and x[0] != bench], 
#								reverse = bool(preds[bench][1] < 0), key = lambda x: x[1][0]))
#		prefs[bench] += map(lambda x: x[0],
#						sorted([x for x in preds.items() if x[1][1] * preds[bench][0] > 0 and x[0] != bench],
#								reverse = bool(preds[bench][1] < 0), key = lambda x: x[1][0]))
#####Sort by Classes only
#		prefs1[bench] = map(lambda x: x[0],
#						sorted([x for x in preds.items() if x[1][1] == 1 - preds[bench][0] and x[0] != bench],
#								reverse = bool(1 - preds[bench][1]), key = lambda x: x[1][0]))
#		prefs1[bench] += map(lambda x:x[0],
#						sorted([x for x in preds.items() if x[1][1] == preds[bench][0] and x[0] != bench],
#								reverse = bool(1 - preds[bench][1]), key = lambda x: x[1][0]))
	return prefs

def q_predictor_based(benchmarks, real = False):
	predictions = dict()
	features = ['sens', 'cont']
	suffix = '_q_' + str(clos) + '.csv'
	for f in features:
		with open(csv_dir + f + suffix, mode='r') as pred:
			reader = csv.reader(pred, delimiter='\t')
			predictions[f] = dict((rows[0], rows[3]) for rows in reader) if real else dict((rows[0], rows[1]) for rows in reader)
			del predictions[f]['Bench']
			pred.close()
	preds = dict((x, (int(predictions['sens'][x.split('.')[1]]), int(predictions['cont'][x.split('.')[1]]))) for x in benchmarks)
	prefs = dict()
	for bench in benchmarks:
		sens_order = sorted([0, 1, 2], reverse = not bool(preds[bench][0]))
		prefs[bench] = map(lambda x: x[0],
						sorted([x for x in preds.items() if x[1][1] == sens_order[0] and x[0] != bench],
							key = lambda x: x[1][0], reverse = not bool(preds[bench][1])))
		prefs[bench] += map(lambda x: x[0],
						sorted([x for x in preds.items() if x[1][1] == sens_order[1] and x[0] != bench],
							key = lambda x: x[1][0], reverse = not bool(preds[bench][1])))
		prefs[bench] += map(lambda x: x[0],
						sorted([x for x in preds.items() if x[1][1] == sens_order[2] and x[0] != bench],
							key = lambda x: x[1][0], reverse = not bool(preds[bench][1])))
	return prefs

####################################### Custom Pairing Algorithm ##########################################

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

def get_predictions(benchmarks, real, classes):
	predictions = dict()
	features = ['sens', 'cont']
	suffix = '_' + str(clos) + '.csv' if classes == 2 else '_q_' + str(clos) + '.csv'
	for f in features:
		with open(csv_dir + f + suffix, mode='r') as pred:
			reader = csv.reader(pred, delimiter='\t')
			predictions[f] = dict((rows[0], rows[3]) for rows in reader) if real else dict((rows[0], rows[1]) for rows in reader)
			del predictions[f]['Bench']
			pred.close()
	return dict((x, (int(predictions['sens'][x.split('.')[1]]), int(predictions['cont'][x.split('.')[1]]))) for x in benchmarks)

def get_attacker(benchmarks):
	classes = attacker_classifier()
	return dict((x, classes[x.split('.')[1]]) for x in benchmarks)

def custom_based(benchmarks, real = False, classes = 3, attackers = False):
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
	pairs = map(lambda x: [x[0][0], x[1][0]], pairs)
	return pairs

################################################# Printers #################################

def print_prefs(prefs, mode = 'oracle'):
	fd = open(mode + '_prefs.csv', 'w')
	wr = csv.writer(fd, delimiter = ',')
	for p in prefs:
		wr.writerow([p] + prefs[p])
		wr.writerow([p] + [grid[p.split('.')[1]][x.split('.')[1]] for x in prefs[p]])
	fd.close()

def print_sd(pairs):
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
		#print p.split('_')[0] + ',' + p.split('_')[1] + ',' + str(m1) + ',' + str(m2)
	#print "\t\tVIOLATIONS:", violations
	return violations

################################################# Main ###########################################

def fix_pairing(holds):
	pairs = []
	if not holds: return -1
	for bench1 in holds:
		bench2 = holds[bench1]
		if bench2 in [x[0] for x in pairs]: continue
		pairs.append([bench1,bench2])
	violations = print_sd(pairs)
	pairs = map(lambda x: [x[0].split('.')[1], x[1].split('.')[1]], pairs)
	return violations

def decide_pairs(benchmarks, algo, real = True, classes = 2):
	benchmarks = set([str(i) + '.' + x for (i, x) in enumerate(benchmarks)])
	if algo == 'random':
		return random_pairs(benchmarks)
	elif algo == 'oracle':
		prefs = oracle(benchmarks)
	elif algo == 'forest':
		prefs = oracle(benchmarks, 'pred')
	elif algo == 'whisker':
		prefs = whisker_based(benchmarks)
	elif algo == 'predictor':
		if classes == 2: prefs = predictor_based(benchmarks, real)
		if classes == 3: prefs = q_predictor_based(benchmarks, real)
	elif algo == 'custom':
		pairs = custom_based(benchmarks, True, classes)
		violations = print_sd(pairs)
		pairs = map(lambda x: [x[0].split('.')[1], x[1].split('.')[1]], pairs)
		return violations
	elif algo == 'attackers':
		pairs = custom_based(benchmarks, attackers=True)
		violations = print_sd(pairs)
		pairs = map(lambda x: [x[0].split('.')[1], x[1].split('.')[1]], pairs)
		return violations
	#print_prefs(prefs, algo)
	return fix_pairing(stableroommate(prefs))

def manual(args):
	bench_file = wd_dir + args[1] + '.csv'
	algo = args[2]
	if algo in ['predictor', 'custom']:
		try:
			real = args[3] == 'real'
		except:
			real = True
		try:
			classes = int(args[4])
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
	print(pairs)

def print_results(results):
	fd = open('/'.join(csv_dir.split('/')[:-2]) + '/' + 'violations_' + str(clos) + '.csv', 'w')
	wr = csv.writer(fd, delimiter = ',')
	sizes = map(str, sorted(map(int, results.keys())))
	files = results[sizes[0]].keys()[::-1]
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

def loop(args):
	global clos
	clos = float(args[1])
	files = os.listdir(wd_dir)
	files = [x for x in files if x.endswith('.csv')]
	workloads = set(map(lambda x: x.split('-')[0], files))
	sizes = set(map(lambda x: x.split('-')[1].split('.')[0], files))
	algorithms = ['oracle', 'whisker', 'random', 'attackers',
				  #'predictor_real_2', 'predictor_real_3', 'predictor_pred_2', 'predictor_pred_3',
				  'forest', 'custom_real_2', 'custom_real_3', 'custom_pred_2', 'custom_pred_3']
	results = OrderedDict()
	for size in sizes:
		print "Size:", size
		results[size] = OrderedDict()
		for _file in workloads:
			results[size][_file] = OrderedDict()
			print "\tWorkload:", _file
			bench_file = wd_dir + _file + '-' + size + '.csv'
			bench_f = open(bench_file)
			reader = csv.reader(bench_f, delimiter=',')
			benchmarks = [row[0] + '-' + row[1] for row in reader]

			for algo in algorithms:
				print "\t\tAlgorithm:", algo
				if algo in ['oracle', 'forest', 'whisker']:
					violations = [decide_pairs(benchmarks, algo)]
				elif algo == 'random' or algo == 'attackers':
					violations = []
					for i in range(100):
						violations.append(decide_pairs(benchmarks, algo))
				elif algo.startswith('custom'): # 'predictor'
					violations = []
					(algorithm, real, classes) = algo.split('_')
					for i in range(100):
						violations.append(decide_pairs(benchmarks, algorithm, real, int(classes)))
				results[size][_file][algo] = np.mean(violations)
			bench_f.close()
	print_results(results)
			
if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "Usage: m for manual"
		print "loop: clos"
		print "manual: workload, algorithm, real, classes"
		print "algorithms: oracle, forest, attackers, whisker, random, predictor, custom"
		sys.exit(1)
	if sys.argv[1] == 'm': manual(sys.argv[1:])
	else: loop(sys.argv)
