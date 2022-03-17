#!/usr/bin/python3
import random, sys, math, subprocess
from heatmap_reader import *
from isolation_reader import *
from model_selection import csv_writer, print_pred, get_data_name, run_model, help_message

tool = 'perf'
fold = 8

def cross_validation(measures, feature, qos, class_num, model):
	chunksize = int(math.floor(len(measures.keys()) / fold))
	benches = [x for x in measures.keys() if x != 'Title']
	random.shuffle(benches)
	chunks = [benches[i:i + chunksize] for i in range(0, len(benches), chunksize)]
	(classes, whiskers, quartiles) = make_partial_grid(benches, feature, [qos], class_num)

	answers = dict()
	acc_scores = []
	data_name = get_data_name(feature, class_num, model)

	for test_set in chunks:
		train_chunks = [x for x in chunks if x != test_set]
		train_set = [element for lst in train_chunks for element in lst]
		(train_classes, _, _) = make_partial_grid(train_set, feature, [qos], class_num)
		csv_writer(measures, train_classes, train_set, data_name + 'train')
		csv_writer(measures, classes, test_set, data_name + 'test')
		acc_scores.append(run_model(answers, feature, class_num, qos, model))

	os.remove(csv_dir + data_name + 'train.csv')
	os.remove(csv_dir + data_name + 'test.csv')
	if type(model) == str:
		#outfile = csv_dir + feature + '_' + str(class_num) + '_' + str(qos) + '_' + model + '.csv'
		#print_pred(answers, outfile, np.mean(acc_scores))
		print("CV: " + feature + ' | ' + str(qos) + ' | C:' + str(class_num) + ' | ' + model + ' | ' + str(100 * round(np.mean(acc_scores), 4)) + '%')
	return np.mean(acc_scores)

def testing(measures, train, test, feature, qos, class_num, model):
	benches = [x for x in measures.keys() if x != "Title"]
	(classes, whiskers, quartiles) = make_partial_grid(benches, feature, [qos], class_num)
	answers = dict()
	data_name = get_data_name(feature, class_num, model)

	(train_classes, _, _) = make_partial_grid(train, feature, [qos], class_num)
	csv_writer(measures, train_classes, train, data_name + 'train')
	csv_writer(measures, classes, test, data_name + 'test')
	acc_score = run_model(answers, feature, class_num, qos, model)
	os.remove(csv_dir + data_name + 'train.csv')
	os.remove(csv_dir + data_name + 'test.csv')

	if type(model) == str:
		print("TEST: " + feature + ' | ' + str(qos) + ' | C:' + str(class_num) + ' | ' + model + ' | ' + str(100 * round(acc_score, 4)) + '%')

def prediction(func, feature, qos, class_num, model):
	all_benchmarks = subprocess.run(('ls -rt ' + pairs_dir).split(), stdout = subprocess.PIPE).stdout.decode("utf-8").split('\n')
	specs = [x + '-' + y for x in all_benchmarks[:28] for y in vcpus]
	parsecs = [x + '-' + '1' for x in all_benchmarks[28:-1]]
	measures = perf_files(tool)
	if func == 'cv':
		exclude = set(measures.keys()).difference(specs)
		for x in exclude:
			if x != 'Title': del measures[x]
		cross_validation(measures, feature, qos, class_num, model)
	if func == 'test':
		exclude = set(measures.keys()).difference(specs + parsecs)
		for x in exclude:
			if x != 'Title': del measures[x]
		testing(measures, specs, parsecs, feature, qos, class_num, model)

def arg_check(argv):
	(func, feature, qos, class_num, model) = argv
	qos = float(qos)
	class_num = int(class_num)
	if func not in ['cv', 'test'] or \
	   feature not in ['sens', 'cont'] or \
	   qos not in [1 + 0.1 * x for x in range(1, 4)] or \
	   class_num not in [2, 3] or \
	   model not in ["SVC", "DT", "KN", "RF"]: return False
	prediction(func, feature, qos, class_num, model)

if __name__ == '__main__':
	if len(sys.argv) < 6:
		sys.exit(help_message(sys.argv[0]))
	sys.exit(arg_check(sys.argv[1:]))
