#!/usr/bin/python3
import sys
sys.path.append('../predict/')
from attackers import *

contentions = ['l', 'm', 'h']
bench_suites = ['s', 'sp', 'spt'][2]
def pred_file(feature, qos, classes):
	return f"{predictions_dir}SVC/SVC_{feature}_{classes}_{qos}_{bench_suites}_cv.csv"

def workload_filename(contention, size, qos_in):
	cont = {'l': 'low', 'm': 'med', 'h': 'high'}
	return f"{workload_dir}{cont[contention]}-{size}-{qos_in}.csv"

def benchmarks_list(qos, classes):
	(sens_f, cont_f) = [open(pred_file(feature, qos, classes), 'r') for feature in features]

	classes = dict((row[0], row[-1]) for row in csv.reader(sens_f, delimiter = '\t') if row[0] != 'Bench' and row[0] != 'Accuracy')
	for row in csv.reader(cont_f, delimiter = '\t'):
		if row[0] == 'Bench' or row[0] == 'Accuracy': continue
		classes[row[0]] = (int(classes[row[0]]), int(row[-1]))
	groups = dict()
	for (bench, class_) in classes.items():
		if bench.endswith('1'): continue
		index = min(sum(class_), 2)
		if index in groups:
			groups[index].append(bench)
		else: groups[index] = [bench]
	for fd in [sens_f, cont_f]: fd.close()
	return groups

def generate_workload(contention, size, qos_in, classes, printed = True):
	qos = qos_levels if qos_in == 'all' else [float(qos_in)]
	groups = dict((slo, benchmarks_list(slo, classes)) for slo in qos)
	bench_list = []
	(zeros, ones, twos) = (0, 0, 0)
	cont = 2 * int(contention == "h") + int(contention == "m")
	while len(bench_list) < size:
		for c in [0, 1, 2, cont]:
			qos_to_choose = list(filter(lambda x: c in groups[x], qos))
			if not qos_to_choose:
				print(f"No benchmarks with intensity: {c} for qos: {qos}")
				return
			slo = random.choice(qos_to_choose)
			bench_list.append(f"{random.choice(groups[slo][c])},{slo}")
	if printed:
		wl_file = open(workload_filename(contention, size, qos_in), 'w')
		for row in bench_list: wl_file.write(row + '\n')
		wl_file.close()
	return list(set([f"{i},{row[0]},{row[1]}" for (i, row) in enumerate(map(lambda x: x.split(','), bench_list))]))

def arg_check_generate_workload(args):
	if len(args) < 5 or \
	   args[1] not in contentions or \
	   not all([x.isdigit() for x in args[2]]) or \
	   args[3] not in list(map(str, qos_levels)) + ['all'] or \
	   args[4] not in list(map(str, classes_)):
		print(f"Usage:      {args[0]} <contention> <size> <slos> <classes>\n" + \
			  f"Contention: {' | '.join(contentions)}\n" + \
			  f"Size:       int\n" + \
			  f"SLO:        {' | '.join(list(map(str, qos_levels)) + ['all'])}\n" + \
			  f"Classes:    {' | '.join(map(str, classes_))}")
		sys.exit(1)

if __name__ == '__main__':
	arg_check_generate_workload(sys.argv)
	(contention, size, qos, classes) = sys.argv[1:]
	generate_workload(contention, int(size), qos, int(classes))
