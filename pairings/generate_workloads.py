#!/usr/bin/python3
import sys
sys.path.append('../core/')
from read_vm_output import *

def pred_file(feature, qos, classes):
	return f"{predictions_dir}SVC/SVC_{feature}_{classes}_{qos}_sp_cv.csv"

def benchmarks_list(qos, classes):
	(sens_f, cont_f) = [open(pred_file(feature, qos, classes), 'r') for feature in features]

	classes = dict((row[0], row[-1]) for row in csv.reader(sens_f, delimiter = '\t') if row[0] != 'Bench')
	for row in csv.reader(cont_f, delimiter = '\t'):
		if row[0] == 'Bench': continue
		classes[row[0]] = (int(classes[row[0]]), int(row[-1]))
	groups = dict()
	for (bench, class_) in classes.items():
		if bench.endswith('8'): continue
		index = min(sum(class_), 2)
		if index in groups:
			groups[index].append(bench)
		else: groups[index] = [bench]
	return groups

def generate_workload(contention, size, qos_in, classes):
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
	wl_file = open(f"{workload_dir}{contention}-{size}-{qos_in}.csv", 'w')
	for row in bench_list: wl_file.write(row + '\n')
	wl_file.close()

def arg_check(args):
	contentions = ['l', 'm', 'h']
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
	arg_check(sys.argv)
	(contention, size, qos, classes) = sys.argv[1:]
	generate_workload(contention, int(size), qos, int(classes))
