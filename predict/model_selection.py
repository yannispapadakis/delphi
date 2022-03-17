from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

qos1_1 = {('sens', 2): {
			'SVC': SVC(C = 5, kernel = 'poly', degree = 2),
			'DT' : DecisionTreeClassifier(criterion = 'entropy', splitter = 'best', min_samples_split = 6, min_samples_leaf = 4, max_features = 'sqrt'),
			'KN' : KNeighborsClassifier(n_neighbors = 4, weights = 'distance', algorithm = 'kd_tree', leaf_size = 20, p = 1),
			'RF' : RandomForestClassifier(n_estimators = 45, criterion = 'entropy', min_samples_split = 7, min_samples_leaf = 7, max_features = 'sqrt', bootstrap = False)},
		('sens', 3): {
			'SVC': SVC(C = 4, kernel = 'linear', degree = 3),
			'DT' : DecisionTreeClassifier(criterion = 'gini', splitter = 'best', min_samples_split = 9, min_samples_leaf = 4, max_features = 'log2'),
			'KN' : KNeighborsClassifier(n_neighbors = 4, weights = 'distance', algorithm = 'kd_tree', leaf_size = 5, p = 1),
			'RF' : RandomForestClassifier(n_estimators = 50, criterion = 'entropy', min_samples_split = 8, min_samples_leaf = 4, max_features = 'log2', bootstrap = False)},
		('cont', 2): {
			'SVC': SVC(C = 5, kernel = 'linear', degree = 3),
			'DT' : DecisionTreeClassifier(criterion = 'gini', splitter = 'best', min_samples_split = 5, min_samples_leaf = 5, max_features = 'log2'),
			'KN' : KNeighborsClassifier(n_neighbors = 7, weights = 'uniform', algorithm = 'ball_tree', leaf_size = 5, p = 1),
			'RF' : RandomForestClassifier(n_estimators = 35, criterion = 'gini', min_samples_split = 7, min_samples_leaf = 4, max_features = 'log2', bootstrap = True)},
		('cont', 3): {
			'SVC': SVC(C = 9, kernel = 'linear', degree = 3),
			'DT' : DecisionTreeClassifier(criterion = 'gini', splitter = 'best', min_samples_split = 6, min_samples_leaf = 8, max_features = 'log2'),
			'KN' : KNeighborsClassifier(n_neighbors = 7, weights = 'uniform', algorithm = 'kd_tree', leaf_size = 5, p = 1),
			'RF' : RandomForestClassifier(n_estimators = 40, criterion = 'gini', min_samples_split = 8, min_samples_leaf = 4, max_features = 'log2', bootstrap = True)}}

qos1_2 = {('sens', 2): {
			'SVC': SVC(C = 4, kernel = 'linear', degree = 3),
			'DT' : DecisionTreeClassifier(criterion = 'entropy', splitter = 'random', min_samples_split = 2, min_samples_leaf = 2, max_features = None),
			'KN' : KNeighborsClassifier(n_neighbors = 6, weights = 'distance', algorithm = 'ball_tree', leaf_size = 15, p = 3),
			'RF' : RandomForestClassifier(n_estimators = 45, criterion = 'entropy', min_samples_split = 2, min_samples_leaf = 4, max_features = 'log2', bootstrap = False)},
		('sens', 3): {
			'SVC': SVC(C = 8, kernel = 'rbf', degree = 3),
			'DT' : DecisionTreeClassifier(criterion = 'gini', splitter = 'best', min_samples_split = 8, min_samples_leaf = 8, max_features = 'sqrt'),
			'KN' : KNeighborsClassifier(n_neighbors = 8, weights = 'distance', algorithm = 'kd_tree', leaf_size = 15, p = 3),
			'RF' : RandomForestClassifier(n_estimators = 40, criterion = 'entropy', min_samples_split = 5, min_samples_leaf = 4, max_features = 'sqrt', bootstrap = False)},
		('cont', 2): {
			'SVC': SVC(C = 5, kernel = 'poly', degree = 1),
			'DT' : DecisionTreeClassifier(criterion = 'gini', splitter = 'best', min_samples_split = 7, min_samples_leaf = 5, max_features = 'log2'),
			'KN' : KNeighborsClassifier(n_neighbors = 7, weights = 'uniform', algorithm = 'ball_tree', leaf_size = 10, p = 1),
			'RF' : RandomForestClassifier(n_estimators = 40, criterion = 'gini', min_samples_split = 6, min_samples_leaf = 4, max_features = 'log2', bootstrap = True)},
		('cont', 3): {
			'SVC': SVC(C = 2, kernel = 'linear', degree = 3),
			'DT' : DecisionTreeClassifier(criterion = 'gini', splitter = 'best', min_samples_split = 4, min_samples_leaf = 6, max_features = 'log2'),
			'KN' : KNeighborsClassifier(n_neighbors = 7, weights = 'uniform', algorithm = 'ball_tree', leaf_size = 10, p = 1),
			'RF' : RandomForestClassifier(n_estimators = 45, criterion = 'entropy', min_samples_split = 4, min_samples_leaf = 5, max_features = 'log2', bootstrap = True)}}

def select_model(mod, feature, cl, qos):
	if qos <= 1.15:
		return qos1_1[(feature, cl)][mod]
	else:
		return qos1_2[(feature, cl)][mod]

#-------------------- Tools --------------------
import csv
import pandas as pd
from sklearn import preprocessing
from heatmap_reader import csv_dir

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

def get_data_name(feature, cl, mod):
	if type(mod) == str:
		return feature + str(cl) + mod
	modd = str(type(mod)).split('.')[-1].split("'")[0]
	if modd == 'DecisionTreeClassifier': modd = 'DT'
	if modd == 'KNeighbors': modd = 'KN'
	if modd == 'RandomForest': modd = 'RF'
	return feature + str(cl) + modd

def run_model(answers, feature, cl, qos, mod = 'SVC'):
	train_data = pd.read_csv(csv_dir + get_data_name(feature, cl, mod) + 'train.csv')
	test_data = pd.read_csv(csv_dir + get_data_name(feature, cl, mod) + 'test.csv')

	if feature == 'cont': remove_cols = [0, 2, 3, 4, 5, 6, 8, 15]
	if feature == 'sens': remove_cols = [0, 8, 13, 15]
	train = train_data.drop(train_data.columns[remove_cols], axis = 1)
	test = test_data.drop(test_data.columns[remove_cols], axis = 1)

	scaler = preprocessing.StandardScaler().fit(train)

	train_names = train_data['Benchmark']
	test_names = test_data['Benchmark']
	y_train = train_data['Class']
	y_test = test_data['Class']

	if type(mod) == str:
		model = select_model(mod, feature, cl, qos)
	else: model = mod

	train_scaled = scaler.transform(train)
	test_scaled = scaler.transform(test)
	try:
		model.fit(train_scaled, y_train)
	except ValueError:
		return 0

	test_pred = model.predict(test_scaled)
	acc_score = model.score(test_scaled, y_test)

	for i in range(len(test_names)):
		answers[test_names[i]] = (test_pred[i], y_test[i])
	return acc_score

def help_message(ex):
	msg =  "Usage:    %s <function> <feature> <qos> <classes> <model>\n" % ex
	msg += "Function: " + ' | '.join(['test', 'cv']) + '\n'
	msg += "Feature:  " + ' | '.join(['sens', 'cont']) + '\n'
	msg += "QoS:      " + ' | '.join(map(str, [1 + 0.1 * x for x in range(1, 4)])) + "\n"
	msg += "Classes:  " + ' | '.join(['2', '3']) + '\n'
	msg += "Model:    " + ' | '.join(['SVC', 'DT', 'KN', 'RF'])
	print(msg)
	return 0

