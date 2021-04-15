from sklearn.ensemble import RandomForestRegressor 
import pandas as pd
import sys
sys.path.append('../perf_runs/')
from perf_reader import *
sys.path.append('../grid_runs/')
from grid import *
import random

def pair_perf(measures):
	pair_measures = []

	grid = generate_grid()
	read_grid(grid)

	for bench1 in grid:
		perf1 = measures[bench1]
		for bench2 in grid[bench1]:
			perf2 = measures[bench2]
			pair = perf1[0] + '_' + perf2[0]
			perfs = perf1[1:] + perf2[1:]
			sd = grid[bench1][bench2]
			row = [pair] + perfs + [sd]
			pair_measures.append(row)
	return pair_measures

def csv_writer(pair_measures, train_set, test_set, title):
	train_file = csv_dir + 'train.csv'
	train_fd = open(train_file, mode = 'w')
	train = csv.writer(train_fd, delimiter = ',')
	test_file = csv_dir + 'test.csv'
	test_fd = open(test_file, mode = 'w')
	test = csv.writer(test_fd, delimiter = ',')
	
	train.writerow(title)
	test.writerow(title)

	for row in pair_measures:
		(b1, b2) = row[0].split('_')
		if b1 in train_set and b2 in train_set:
			train.writerow(row)
		elif b1 in test_set:
			test.writerow(row)

	train_fd.close()
	test_fd.close()

def predicted_grid(answers):
	grid = generate_grid()
	for pair in answers:
		(bench1, bench2) = pair.split('_')
		grid[bench1][bench2] = answers[pair][0]
	return grid

def random_forest(answers):
	train_data = pd.read_csv(csv_dir + 'train.csv')
	test_data = pd.read_csv(csv_dir + 'test.csv')
	
	#remove_cols = [0,8,10,13,21,23,26,27] # Benchmark, IPC (perf), IPC (pqos), LLC Misses, Slowdown
	remove_cols = [0, 8, 16, 17] # Benchmark, IPC (1), IPC (2), Slowdown
	train = train_data.drop(train_data.columns[remove_cols], axis = 1)
	test = test_data.drop(test_data.columns[remove_cols], axis = 1)

	train_names = train_data['Benchmark']
	test_names = test_data['Benchmark']
	y_train = train_data['Slowdown']
	y_test = test_data['Slowdown']

	# Random Forest Model. min_samples_split = 2, bootstrap = True (by default)
	model = RandomForestRegressor(max_features = 'sqrt', n_estimators = 22)
	try:
		model.fit(train, y_train)
	except:
		print "RandomForest Error"
		return False
	test_pred = model.predict(test)
	r2 = model.score(test, y_test) # return the coefficient of determination R^2 of the prediction

	for i in range(len(test_names)):
		answers[test_names[i]] = (test_pred[i], y_test[i])
	return r2

def predict(fold = 5):
	measures = perf_files('perf-sp')
	benchmarks = [x for x in measures.keys() if x != 'Title']
	chunksize = int(np.ceil(len(benchmarks) / float(fold)))
	random.shuffle(benchmarks)
	chunks = [benchmarks[i:i + chunksize] for i in range(0, len(benchmarks), chunksize)]
	answers = dict()
	r2 = []

	pair_measures = pair_perf(measures)
	for test_set in chunks:
		train_chunks = [x for x in chunks if x != test_set]
		train_set = [element for lst in train_chunks for element in lst]
		csv_writer(pair_measures, train_set, test_set, measures['Title'])
		r2.append(random_forest(answers))

	os.remove(csv_dir + 'train.csv')
	os.remove(csv_dir + 'test.csv')
	
	pred_grid = predicted_grid(answers)
	print_ans(answers, r2)
	print_grid(pred_grid, name = 'pred_grid')

def print_ans(answers, r2):
	fd = open(csv_dir + 'random_forest.csv', 'w')
	wr = csv.writer(fd, delimiter = ',')
	diff = []
	for x in answers:
		diff.append(abs(answers[x][1] - answers[x][0]))
		wr.writerow(answers[x])
	fd.close()
	q1 = np.percentile(diff, 25)
	q3 = np.percentile(diff, 75)
	lower_whisker = min([x for x in diff if x >= q1 - 1.5 * (q3 - q1)])
	upper_whisker = max([x for x in diff if x <= q3 + 1.5 * (q3 - q1)])
	print "Average:    ", np.mean(diff)
	print "Min:        ", min(diff)
	print "L. Whisker: ", lower_whisker
	print "Quartile 1: ", q1
	print "Median:     ", np.percentile(diff, 50)
	print "Quartile 3: ", q3
	print "U. Whisker: ", upper_whisker
	print "Max:        ", max(diff)
	print "R2 Scores:"
	pprint.pprint(r2)

if __name__ == '__main__':
	predict()
