#!/usr/bin/python3
from sklearn.ensemble import RandomForestRegressor 
import pandas as pd
from heatmap import *

temp_dir = '/home/ypap/temp/'

def pair_perf(measures):
	benchmarks = list(filter(lambda x: x != 'Title', list(measures.keys())))
	pair_measures = []
	heatmap = spawn_heatmap(benchmarks)
	read_heatmap(heatmap)

	for bench1 in heatmap:
		perf1 = measures[bench1]
		for bench2 in heatmap[bench1]:
			perf2 = measures[bench2]
			pair_measures.append([f"{perf1[0]}_{perf2[0]}"] + perf1[1:] + perf2[1:] + [heatmap[bench1][bench2]])
	return pair_measures

def csv_writer(pair_measures, train_set, test_set, title):
	train_file = temp_dir + 'train.csv'
	with open(f"{temp_dir}train.csv", mode = 'w') as train_fd:
		train = csv.writer(train_fd, delimiter = ',')
		with open(f"{temp_dir}test.csv", mode = 'w') as test_fd:
			test = csv.writer(test_fd, delimiter = ',')

			train.writerow(title)
			test.writerow(title)
			for row in pair_measures:
				(b1, b2) = row[0].split('_')
				if b1 in train_set and b2 in train_set:
					train.writerow(row)
				elif b1 in test_set:
					test.writerow(row)

def predicted_heatmap(answers):
	heatmap = spawn_heatmap()
	for pair in answers:
		(bench1, bench2) = pair.split('_')
		heatmap[bench1][bench2] = answers[pair][0]
	clean_heatmap(heatmap)
	return heatmap

def random_forest(answers):
	train_data = pd.read_csv(f"{temp_dir}train.csv")
	test_data = pd.read_csv(f"{temp_dir}test.csv")
	
	remove_cols = [0, 18] # Benchmark, Slowdown
	train = train_data.drop(train_data.columns[remove_cols], axis = 1)
	test = test_data.drop(test_data.columns[remove_cols], axis = 1)

	train_names = train_data['Benchmark']
	test_names = test_data['Benchmark']
	y_train = train_data['Slowdown']
	y_test = test_data['Slowdown']

	# Random Forest Model. min_samples_split = 2, bootstrap = True (by default)
	model = RandomForestRegressor(max_features = 'sqrt', n_estimators = 22)
	try: model.fit(train, y_train)
	except:
		print("RandomForest Error")
		return False
	test_pred = model.predict(test)
	r2 = model.score(test, y_test) # return the coefficient of determination R^2 of the prediction

	for i in range(len(test_names)):
		answers[test_names[i]] = (test_pred[i], y_test[i])
	return r2

def predict(fold = 5):
	measures = perf_files('perf-sp')
	benchmarks = list(filter(lambda x: x != 'Title', list(measures.keys())))
	chunksize = int(np.ceil(len(benchmarks) / float(fold)))
	random.shuffle(benchmarks)
	chunks = [benchmarks[i:i + chunksize] for i in range(0, len(benchmarks), chunksize)]
	answers = dict()
	r2 = []

	pair_measures = pair_perf(measures)
	for test_set in chunks:
		train_chunks = [x for x in chunks if x != test_set]
		train_set = [bench for chunk in train_chunks for bench in chunk]
		csv_writer(pair_measures, train_set, test_set, measures['Title'])
		r2.append(random_forest(answers))

	os.remove(temp_dir + 'train.csv')
	os.remove(temp_dir + 'test.csv')
	
	pred_heatmap = predicted_heatmap(answers)
	print_ans(answers, r2)
	print_heatmap(pred_heatmap, name = 'pred_heatmap')

def print_ans(answers, r2):
	with open(f"{temp_dir}random_forest.csv", 'w') as fd:
		writer = csv.writer(fd, delimiter = ',')
		writer.writerow(['Pair', 'Predicted', 'Real'])
		for x in answers: writer.writerow([x] + list(answers[x]))
	diff = [abs(answers[x][1] - answers[x][0]) for x in answers]
	q1 = np.percentile(diff, 25)
	q3 = np.percentile(diff, 75)
	lower_whisker = min([x for x in diff if x >= q1 - 1.5 * (q3 - q1)])
	upper_whisker = max([x for x in diff if x <= q3 + 1.5 * (q3 - q1)])
	report = f"Average:  {np.mean(diff):.4f}\n" + \
			 f"Min:      {min(diff):.4f}\n" + \
			 f"L. Fence: {lower_whisker:.4f}\n" + \
			 f"Quart. 1: {q1:.4f}\n" + \
			 f"Median:   {np.percentile(diff, 50):.4f}\n" + \
			 f"Quart. 3: {q3:.4f}\n" + \
			 f"U. Fence: {upper_whisker:.4f}\n" + \
			 f"Max:      {max(diff):.4f}\n" + \
			 f"R^2:      {gmean(r2)}"
			 #f"R^2:      {' | '.join(map(str, r2))}"
	print(report)

import matplotlib.pyplot as plt
def map_graph():
	df = pd.read_csv(f"{temp_dir}random_forest.csv")
	fig = plt.figure(figsize = (21,15))
	plt.scatter(df['Real'], df['Predicted'], s = 10)
	plt.ylim(1.0, 2.0)
	plt.xlim(1.0, 2.0)
	plt.plot([0,5],[0,5], marker = 'o', color='red')
	plt.savefig(f"{results_dir}randomforest.png")

if __name__ == '__main__':
	predict(5)
	map_graph()
