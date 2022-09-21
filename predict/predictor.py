#!/usr/bin/python3
from itertools import product
from models_backend import *

tool = 'perf'
fold = 8

def cross_validation(measures, feature, qos, class_num, model):
	chunksize = int(math.floor(len(measures.keys()) / fold))
	benches = [x for x in measures.keys() if x != 'Title']
	random.shuffle(benches)
	chunks = [benches[i:i + chunksize] for i in range(0, len(benches), chunksize)]
	(classes, whiskers, quartiles) = get_heatmap(benches, feature, qos, class_num)

	answers = dict()
	acc_scores = []
	data_name = get_data_name(feature, class_num, model, qos)

	for test_set in chunks:
		train_chunks = [x for x in chunks if x != test_set]
		train_set = [element for lst in train_chunks for element in lst]
		(train_classes, _, _) = get_heatmap(train_set, feature, qos, class_num)
		pred_set_writer(measures, train_classes, train_set, data_name + 'train')
		pred_set_writer(measures, classes, test_set, data_name + 'test')
		acc_scores.append(run_model(answers, feature, class_num, qos, model))

	os.remove(temp_dir + data_name + 'train.csv')
	os.remove(temp_dir + data_name + 'test.csv')
	if type(model) == str:
		print("CV: " + feature + ' | ' + str(qos) + ' | C:' + str(class_num) + ' | ' + model + ' ' * (4 - len(model)) + ' | ' + str(100 * round(np.mean(acc_scores), 4)) + '%')
	return (np.mean(acc_scores), answers)

def testing(measures, train, test, feature, qos, class_num, model):
	benches = [x for x in measures.keys() if x != "Title"]
	(classes, whiskers, quartiles) = get_heatmap(benches, feature, qos, class_num)
	answers = dict()
	data_name = get_data_name(feature, class_num, model, qos)

	(train_classes, _, _) = get_heatmap(train, feature, qos, class_num)
	pred_set_writer(measures, train_classes, train, data_name + 'train')
	pred_set_writer(measures, classes, test, data_name + 'test')
	acc_score = run_model(answers, feature, class_num, qos, model)
	os.remove(temp_dir + data_name + 'train.csv')
	os.remove(temp_dir + data_name + 'test.csv')

	if type(model) == str:
		print_pred(answers, results_dir + 'predictions/' + model + '/' + '_'.join([model, feature, str(class_num), str(qos), 'test']) + '.csv', acc_score)
		print("TEST: " + feature + ' | ' + str(qos) + ' | C:' + str(class_num) + ' | ' + model + ' ' * (4 - len(model))+ ' | ' + str(100 * round(acc_score, 4)) + '%')

def prediction(args):
	measures = perf_files(tool)
	(func, feature, qos, class_num, model) = args[:5]
	if func == 'cv':
		train = get_train_test(args[5])
		exclude = set(measures.keys()).difference(train)
		for x in exclude:
			if x != 'Title': del measures[x]
		return cross_validation(measures, feature, float(qos), int(class_num), model)
	if func == 'test':
		(train, test) = args[5:]
		(train, test) = get_train_test(train, test)
		exclude = set(measures.keys()).difference(train + test)
		for x in exclude:
			if x != 'Title': del measures[x]
		testing(measures, train, test, feature, float(qos), int(class_num), model)

if __name__ == '__main__':
	arg_check(sys.argv)
	prediction(sys.argv[1:])
