#!/usr/bin/python3
import random, math, subprocess
from heatmap_reader import *
from isolation_reader import *
from models_backend import *

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

def prediction(args):
	(func, feature, qos, class_num, model) = args
	all_benchmarks = subprocess.run(('ls -rt ' + pairs_dir).split(), stdout = subprocess.PIPE).stdout.decode("utf-8").split('\n')
	specs = [x + '-' + y for x in all_benchmarks[:28] for y in vcpus]
	parsecs = [x + '-' + y for x in all_benchmarks[28:-1] for y in vcpus if x != "img-dnn"]
	measures = perf_files(tool)
	if func == 'cv':
		exclude = set(measures.keys()).difference(specs)
		for x in exclude:
			if x != 'Title': del measures[x]
		return cross_validation(measures, feature, float(qos), int(class_num), model)
	if func == 'test':
		exclude = set(measures.keys()).difference(specs + parsecs)
		for x in exclude:
			if x != 'Title': del measures[x]
		testing(measures, specs, parsecs, feature, float(qos), int(class_num), model)

if __name__ == '__main__':
	arg_check(sys.argv)
	prediction(sys.argv[1:])
