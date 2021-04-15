import pandas as pd
import random, pprint, sys
sys.path.append('../grid_runs/')
sys.path.append('../perf_runs/')
from sklearn import preprocessing
from sklearn.svm import SVC
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

def run_model(tool, answers, feature):
	train_data = pd.read_csv(csv_dir + 'train.csv')
	test_data = pd.read_csv(csv_dir + 'test.csv')

	if tool == "pqos": remove_cols = [0, 7]
	if tool == "pcm": remove_cols = [0, 38]
	if tool == "perf" and feature == 'cont':
		remove_cols = [0, 2, 3, 4, 5, 6, 8, 15]
	if tool == "perf" and feature == 'sens':
		remove_cols = [0, 8, 13, 15]
	train = train_data.drop(train_data.columns[remove_cols], axis = 1)
	test = test_data.drop(test_data.columns[remove_cols], axis = 1)

	scaler = preprocessing.StandardScaler().fit(train)

	train_names = train_data['Benchmark']
	test_names = test_data['Benchmark']
	y_train = train_data['Class']
	y_test = test_data['Class']

	model = SVC(kernel='rbf', C=10, gamma='scale', probability=True)

	train_scaled = scaler.transform(train)
	test_scaled = scaler.transform(test)
	try:
		model.fit(train_scaled, y_train)
	except ValueError:
		print "Only 1 class provided"
		return False

	test_pred = model.predict(test_scaled)
	prob = model.decision_function(test_scaled)

	for i in range(len(test_names)):
		answers[test_names[i]] = (test_pred[i], prob[i], y_test[i])
	return True

def print_pred(answers, outfile, whiskers, quartiles, clos):
	fd = open(outfile,'w')
	buckets = dict()
	for c in set([x[2] for x in answers.values()]):
		buckets[c] = (0, 0)
	writer = csv.writer(fd, delimiter='\t')
	correct = 0
	writer.writerow(['Bench', 'Prediction', 'Dec. Func', 'Real', 'Whisker', 'Q3'])
	for x in answers:
		(pred, prob, real) = answers[x]
		buckets[pred] = (buckets[pred][0] + 1, buckets[pred][1])
		buckets[real] = (buckets[real][0], buckets[real][1] + 1)
		whisker = round(whiskers[x],2)
		quartile3 = round(quartiles[x], 2)
		row = [x, pred, prob, real, whisker, quartile3]
		if pred != real:
			try:
				real_class = clos[real]
			except:
				real_class = clos[-1]
			row += [round(abs(whisker - real_class), 2)]
		correct += int(pred == real)
		writer.writerow(row)
	accuracy = (float(correct) * 100) / len(answers.keys())
	writer.writerow(['Accuracy', str(accuracy) + '%'] + buckets.values())
	print 'Accuracy: ' + str(accuracy) + '%'
	fd.close()
	return accuracy

def predict(fold = 8, clos = [1.2] , tool = 'pqos', feature = 'sens', q = ''):
	print "Feature: " + feature + ', CLoS: ' + ','.join([str(x) for x in clos]) + ', tool: ' + tool
	measures = perf_files(tool)
	chunksize = len(measures.keys()) / fold
	benches = [x for x in measures.keys() if x != 'Title']
	random.shuffle(benches)
	chunks = [benches[i:i + chunksize] for i in range(0, len(benches), chunksize)]
	(classes, whiskers, quartiles) = make_grid(feature, clos, q)

	answers = dict()

	for test_set in chunks:
		train_chunks = [x for x in chunks if x != test_set]
		train_set = [element for lst in train_chunks for element in lst]
		(train_classes, _, _) = make_partial_grid(train_set, feature, clos, q)
		csv_writer(measures, train_classes, train_set, 'train')
		csv_writer(measures, classes, test_set, 'test')
		success = run_model(tool, answers, feature)
		if not success:
			return 0

	q_str = '_q' if q else ''
	outfile = csv_dir + feature + q_str + '_' + ','.join([str(x) for x in clos]) + '.csv'
	acc = print_pred(answers, outfile, whiskers, quartiles, clos)
	os.remove(csv_dir + 'train.csv')
	os.remove(csv_dir + 'test.csv')
	return acc

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print 'Arguments: feature (sens/cont), qos (csv), q (for quartiles)'
		sys.exit(1)
	tool = 'perf'
	feature = sys.argv[1]
	k = 8
	qos = sorted(map(float, sys.argv[2].split(',')))
	try:
		q = sys.argv[3]
		if q == 'q':
			predict(k, qos, tool, feature, q)
		else:
			raise AssertionError
	except:
		predict(k, qos, tool, feature)

