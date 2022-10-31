#!/usr/bin/python3
from models_backend import *

tool = 'perf'
fold = 8

def prediction(args):
	(func, feature, qos, class_num, model, train, test) = args

	answers = dict()
	acc_scores = []
	if type(model) == str:
		if train == 's': trained_with = 'spec/'
		elif train == 's,p': trained_with = 'spec-parsec/'
		else:
			print(f"Models have not been trained with {train} yet")
			return
		model = select_model(model, feature, class_num, qos, trained_with)
	data_name = get_data_name(feature, class_num, model, qos, func)

	measures = perf_files(tool)
	(train_set, test_set) = get_train_test(train, test)
	exclude = set(measures.keys()).difference(train_set + test_set)
	for x in filter(lambda x: x != 'Title', exclude): del measures[x]
	benches = list(filter(lambda x: x != 'Title', measures.keys()))
	random.shuffle(benches)
	(classes, whiskers, quartiles) = get_heatmap(benches, feature, qos, class_num)

	if func == 'cv':
		chunksize = int(math.floor(len(measures.keys()) / fold))
		chunks = [benches[i:i + chunksize] for i in range(0, len(benches), chunksize)]

		for test_set in chunks:
			train_chunks = [x for x in chunks if x != test_set]
			train_set = [bench for chunk in train_chunks for bench in chunk]
			(train_classes, _, _) = get_heatmap(train_set, feature, qos, class_num)
			pred_set_writer(measures, [(train_set, train_classes), (test_set, classes)], data_name)
			acc_scores.append(run_model(answers, feature, class_num, qos, model, func))

	if func == 'test':
		(train_classes, _, _) = get_heatmap(train_set, feature, qos, class_num)
		pred_set_writer(measures, [(train_set, train_classes), (test_set, classes)], data_name)
		acc_scores.append(run_model(answers, feature, class_num, qos, model, func))

	for x in range(2): os.remove(temp_dir + data_name + str(x) + '.csv')

	if type(args[4]) == str:
		if func == 'test': print_pred(answers, f"{results_dir}predictions/{args[4]}/{'_'.join([args[4], feature, str(class_num), str(qos), train.replace(',','') + '-' + test, func])}.csv", np.mean(acc_scores))
		print(f"{func.upper()}: {feature} | {qos} | C:{class_num} | {args[4]}{' ' * (4 - len(args[4]))} | {100 * round(np.mean(acc_scores), 4)}%")

	return (np.mean(acc_scores), answers)

if __name__ == '__main__':
	prediction(arg_check(sys.argv))
