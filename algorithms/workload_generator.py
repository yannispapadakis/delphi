import sys, csv, pprint, random

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

def generate_workload(qos, classes, contention, size):
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

if __name__ == '__main__':
	if len(sys.argv) < 2: 
		print "Usage: python workload_generator.py <contention: low, med, high> <size>"
		sys.exit(1)
	contention = sys.argv[1]
	generate_workload(1.3, 3, contention, 100)
