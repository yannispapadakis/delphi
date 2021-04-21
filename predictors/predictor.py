import pandas as pd
import random, pprint, sys
sys.path.append('../grid_runs/')
sys.path.append('../perf_runs/')
from sklearn import preprocessing
from grid import *
from perf_reader import *

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

def print_pred(answers, outfile):
	fd = open(outfile,'w')
	writer = csv.writer(fd, delimiter='\t')
	writer.writerow(['Bench', 'Prediction', 'Real'])
	for x in answers:
		(pred, real) = answers[x]
		writer.writerow([x, pred, real])
	fd.close()

from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

def select_model(mod):
	if mod == 'SVC'         : return SVC(kernel='rbf', C=10, gamma='scale', probability=True)
	if mod == 'DecisionTree': return DecisionTreeClassifier(max_features = 'sqrt')
	if mod == 'KNeighbors'  : return KNeighborsClassifier()
	if mod == 'RandomForest': return RandomForestClassifier()

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

	model = select_model(mod)

	train_scaled = scaler.transform(train)
	test_scaled = scaler.transform(test)
	try:
		model.fit(train_scaled, y_train)
	except ValueError:
		print "Only 1 class provided"
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

	outfile = csv_dir + feature + '_' + str(class_num) + '_' + ','.join([str(x) for x in clos]) + '.csv'
	print_pred(answers, outfile)
	os.remove(csv_dir + 'train.csv')
	os.remove(csv_dir + 'test.csv')
	print feature + ' | ' + ','.join([str(x) for x in clos]) + ' | C:' + str(class_num) + ' | ' + mod + ' | ' + str(100 * round(np.mean(acc_scores), 4)) + '%'
	return np.mean(acc_scores)

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print 'Arguments: feature (sens/cont), qos (csv), number of classes (2 or 3)'
		sys.exit(1)
	feature = sys.argv[1]
	mod = 'SVC'
	qos = sorted(map(float, sys.argv[2].split(',')))
	try:
		class_num = int(sys.argv[3])
		if class_num != 2 and class_num != 3:
			class_num = 2
	except:
		class_num = 2
	predict(qos, feature, mod, class_num)

