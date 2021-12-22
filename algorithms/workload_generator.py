#!/usr/bin/python
import sys, csv, pprint, random, os

predictions_dir = '/home/ypap/characterization/results/predictions/SVC/'

def pred_file(mode, qos, classes):
	return predictions_dir + mode + '_' + str(classes) + '_' + str(qos) + '_SVC.csv'

def benchmarks_list(qos, classes):
	sens_file = open(pred_file('sens', qos, classes), 'r')
	cont_file = open(pred_file('cont', qos, classes), 'r')

	classes = dict((row[0], row[-1]) for row in csv.reader(sens_file, delimiter = '\t'))
	classes.pop('Accuracy', None)
	classes.pop('Bench', None)
	for row in csv.reader(cont_file, delimiter = '\t'):
		if row[0] == 'Bench' or row[0] == 'Accuracy': continue
		classes[row[0]] = (int(classes[row[0]]), int(row[-1]))
	groups = dict()
	for (bench, class_) in classes.items():
		if bench.endswith('8'): continue
		index = min(sum(class_), 2)
		if index in groups:
			groups[index].append(bench)
		else: groups[index] = [bench]
	return groups

def single_slo(qos, classes, contention, size):
	groups = benchmarks_list(qos, classes)
	bench_list = []
	if contention == 'low': cont = 0
	if contention == 'med': cont = 1
	if contention == 'high': cont = 2
	while len(bench_list) < size:
		for c in groups:
			bench_list.append(random.choice(groups[c]).replace('-',','))
		bench_list.append(random.choice(groups[cont]).replace('-',','))
	workload_dir = '/home/ypap/characterization/algorithms/workload_pairs/'
	wl_file = open(workload_dir + contention + '-' + str(size) + '.csv', 'w')
	for row in bench_list:
		wl_file.write(row + '\n')
	wl_file.close()

def multiple_slos(classes, contention, size):
	slos = sorted(map(lambda x: float(x.split('_')[2]), 
				  filter(lambda x: x.startswith('sens_' + str(classes)),
				  os.listdir(predictions_dir))))
	groups = dict()
	for qos in slos:
		groups[qos] = benchmarks_list(qos, classes)
	bench_list = []
	zeros = ones = twos = 0
	if contention == 'low': cont = 0
	if contention == 'med': cont = 1
	if contention == 'high': cont = 2
	while len(bench_list) < size:
		for c in [0, 1, 2]:
			slo = random.choice(slos)
			bench_list.append(random.choice(groups[random.choice(slos)][c]).replace('-', ',') + ',' + str(slo))
		slo = random.choice(slos)
		bench_list.append(random.choice(groups[random.choice(slos)][cont]).replace('-', ',') + ',' + str(slo))
	workload_dir = '/home/ypap/characterization/algorithms/workload_pairs/'
	wl_file = open(workload_dir + contention + '-' + str(size) + '-multSLO.csv', 'w')
	for row in bench_list:
		wl_file.write(row + '\n')
	wl_file.close()

def help_message(ex):
	msg =  "Usage:  %s <contention> <size> <slos> <classes>\n" % ex
	msg += "contention: " + ' | '.join(['low', 'med', 'high']) + '\n'
	msg += "size:       " + 'int\n'
	msg += "slo:        " + ' | '.join(['float: single SLO', 'all: all SLOs']) + '\n'
	msg += "classes:    " + ' | '.join(["2", "3"])
	print(msg)

if __name__ == '__main__':
	if len(sys.argv) < 3:
		sys.exit(help_message(sys.argv[0]))
	contention = sys.argv[1]
	try:
		size = int(sys.argv[2])
	except:
		size = 100
	try:
		classes = int(sys.argv[4])
	except:
		classes = 2
	try:
		qos = sys.argv[3]
		if qos == "all":
			multiple_slos(classes, contention, size)
		elif float(qos) in [1.1, 1.2, 1.3]:
			single_slo(float(qos), classes, contention, size)
	except:
		multiple_slos(classes, contention, size)
