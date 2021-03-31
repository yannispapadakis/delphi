from sklearn.ensemble import RandomForestRegressor 
import pandas as pd
import sys
sys.path.append('../perf_runs/')
from perf_reader import *
sys.path.append('../grid_runs/')
from grid import *
import random

def pair_perf():
	measures = perf_files('perf')
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

def csv_writer(rows, mode):
	out_file = csv_dir + mode + '.csv'
	fd = open(out_file, mode = 'w')
	writer = csv.writer(fd, delimiter = ',')

	measures = perf_files('perf')
	writer.writerow(measures['Title'])

	for row in rows:
		writer.writerow(row)

	fd.close()	

def predicted_grid(answers):
	grid = generate_grid()
	for pair in answers:
		(bench1, bench2) = pair.split('_')
		grid[bench1][bench2] = answers[pair]
	return grid

def random_forest(answers):
	train_data = pd.read_csv(csv_dir + 'train.csv')
	test_data = pd.read_csv(csv_dir + 'test.csv')

	remove_cols = [0, 19]
	train = train_data.drop(train_data.columns[remove_cols], axis = 1)
	test = test_data.drop(test_data.columns[remove_cols], axis = 1)

	train_names = train_data['Bench']
	test_names = test_data['Bench']
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
	print r2

	for i in range(len(test_names)):
		answers[test_names[i]] = test_pred[i]
	return True

def predict(fold = 5):
	pair_measures = pair_perf()
	chunksize = int(np.ceil(len(pair_measures) / float(fold)))
	random.shuffle(pair_measures)
	chunks = [pair_measures[i:i + chunksize] for i in range(0, len(pair_measures), chunksize)]
	answers = dict()

	for test_set in chunks:
		train_chunks = [x for x in chunks if x != test_set]
		train_set = [element for lst in train_chunks for element in lst]
		csv_writer(train_set, 'train')
		csv_writer(test_set, 'test')
		success = random_forest(answers)
		if not success: return 0
	
	os.remove(csv_dir + 'train.csv')
	os.remove(csv_dir + 'test.csv')
	for b in answers:
		print b, '\t', answers[b]
		pass
	
	pred_grid = predicted_grid(answers)
	print_grid(pred_grid, name = 'pred_grid')

if __name__ == '__main__':
	predict()
