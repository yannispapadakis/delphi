import pandas as pd
import random, pprint, sys
sys.path.append('../grid_runs/')
sys.path.append('../perf_runs/')
from sklearn import preprocessing
from grid import *
from perf_reader import *
from datetime import datetime

from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

def csv_writer(measures, classes, benches, mode):
	out_file = csv_dir + mode + '.csv'

	fd = open(out_file, mode='w')
	writer = csv.writer(fd, delimiter=',')

	writer.writerow(measures['Title'])
	for bench in benches:
		if bench in measures and bench in classes:
			outrow = measures[bench] + [classes[bench]]
			writer.writerow(outrow)
	fd.close()

def print_pred(answers, outfile, acc):
	fd = open(outfile,'w')
	writer = csv.writer(fd, delimiter='\t')
	writer.writerow(['Bench', 'Prediction', 'Real'])
	checker = dict()
	for x in answers:
		(pred, real) = answers[x]
		if (pred, real) not in checker:
			checker[(pred, real)] = 1
		else:
			checker[(pred, real)] += 1
		writer.writerow([x, pred, real])
	last_row = ["Accuracy", str(acc) +' '+ str(checker)]
	writer.writerow(last_row)
	fd.close()

def select_model(mod, feature):
	if mod == 'SVC':
		if feature == 'sens':
			return SVC(kernel='linear', C=1)
		if feature == 'cont':
			return SVC(kernel='linear', C=0.9)
	if mod == 'DT':
		if feature == 'sens':
			return DecisionTreeClassifier(criterion='entropy',splitter='random',min_samples_leaf=2)
		if feature == 'cont':
			return DecisionTreeClassifier(min_samples_split=7, min_samples_leaf=5, max_features='log2')
	if mod == 'KN':
		if feature == 'sens':
			return KNeighborsClassifier(n_neighbors=6, weights='distance', algorithm='ball_tree', leaf_size=15, p=3)
		if feature == 'cont':
			return KNeighborsClassifier(n_neighbors=7, weights='uniform', algorithm='ball_tree', leaf_size=10, p=1)
	if mod == 'RF':
		if feature == 'sens':
			return RandomForestClassifier(n_estimators=50, criterion='entropy', min_samples_split=9, min_samples_leaf=5, max_features='log2')
		if feature == 'cont':
			return RandomForestClassifier(n_estimators=40, min_samples_split=6, min_samples_leaf=4, max_features='log2')

def run_model(answers, feature, mod = 'SVC'):
	train_data = pd.read_csv(csv_dir + 'train.csv')
	test_data = pd.read_csv(csv_dir + 'test.csv')

	if feature == 'cont':
		remove_cols = [0, 2, 3, 4, 5, 6, 8, 15]
	if feature == 'sens':
		remove_cols = [0, 8, 13, 15]
	train = train_data.drop(train_data.columns[remove_cols], axis = 1)
	test = test_data.drop(test_data.columns[remove_cols], axis = 1)

	scaler = preprocessing.StandardScaler().fit(train)

	train_names = train_data['Benchmark']
	test_names = test_data['Benchmark']
	y_train = train_data['Class']
	y_test = test_data['Class']

	if type(mod) == str:
		model = select_model(mod, feature)
	else: model = mod

	train_scaled = scaler.transform(train)
	test_scaled = scaler.transform(test)
	try:
		model.fit(train_scaled, y_train)
	except ValueError:
		#print "Only 1 class provided"
		return 0

	test_pred = model.predict(test_scaled)
	acc_score = model.score(test_scaled, y_test)

	for i in range(len(test_names)):
		answers[test_names[i]] = (test_pred[i], y_test[i])
	return acc_score

def predict(clos = [1.2] , feature = 'sens', mod = 'SVC', class_num = 2):
	fold = 8
	tool = 'perf'
	measures = perf_files(tool)
	chunksize = len(measures.keys()) / fold
	benches = [x for x in measures.keys() if x != 'Title']
	random.shuffle(benches)
	chunks = [benches[i:i + chunksize] for i in range(0, len(benches), chunksize)]
	(classes, whiskers, quartiles) = make_grid(feature, clos, class_num)

	answers = dict()
	acc_scores = []

	for test_set in chunks:
		train_chunks = [x for x in chunks if x != test_set]
		train_set = [element for lst in train_chunks for element in lst]
		(train_classes, _, _) = make_partial_grid(train_set, feature, clos, class_num)
		csv_writer(measures, train_classes, train_set, 'train')
		csv_writer(measures, classes, test_set, 'test')
		acc_scores.append(run_model(answers, feature, mod))

	os.remove(csv_dir + 'train.csv')
	os.remove(csv_dir + 'test.csv')
	if type(mod) == str:
		outfile = csv_dir + feature + '_' + str(class_num) + '_' + ','.join([str(x) for x in clos]) + '_' + mod + '.csv'
		print_pred(answers, outfile, np.mean(acc_scores))
		print(feature + ' | ' + ','.join([str(x) for x in clos]) + ' | C:' + str(class_num) + ' | ' + mod + ' | ' + str(100 * round(np.mean(acc_scores), 4)) + '%')
	return np.mean(acc_scores)

def help_message(ex):
	msg =  "Usage:   python %s <feature> <qos> <classes> <model>\n" % ex
	msg += "Feature: " + ' | '.join(['sens', 'cont']) + '\n'
	msg += "QoS:     comma separated float list\n"
	msg += "Classes: " + ' | '.join(['2', '3']) + '\n'
	msg += "Model:   " + ' | '.join(['SVC', 'DT', 'KN', 'RF'])
	print(msg)
	return 0

def arg_check(argv):
	feature = argv[0]
	qos = sorted(map(float, argv[1].split(',')))
	class_num = int(argv[2])
	mod = argv[3]
	predict(qos, feature, mod, class_num)

if __name__ == '__main__':
	if len(sys.argv) < 5:
		sys.exit(help_message(sys.argv[0]))
	sys.exit(arg_check(sys.argv[1:]))
