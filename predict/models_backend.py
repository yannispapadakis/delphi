from sklearn import preprocessing, metrics
from sklearn.linear_model import LogisticRegression, SGDClassifier, PassiveAggressiveClassifier, Perceptron, RidgeClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.svm import SVC, NuSVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier, RadiusNeighborsClassifier, NearestCentroid, NeighborhoodComponentsAnalysis
from sklearn.pipeline import Pipeline
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.experimental import enable_hist_gradient_boosting
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier, ExtraTreesClassifier, AdaBoostClassifier, HistGradientBoostingClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier

import pandas as pd
from heatmap import *

def model_library(model_str, gp):
	if model_str == "LR":   return LogisticRegression(penalty = gp[0], tol = gp[1], C = gp[2], solver = gp[3], l1_ratio = gp[4], max_iter = gp[5])
	if model_str == "PA":   return PassiveAggressiveClassifier(C = gp[0], tol = gp[1], loss = gp[2])
	if model_str == "SGD":  return SGDClassifier(loss = gp[0], penalty = gp[1], alpha = gp[2], learning_rate = gp[3], eta0 = gp[4], l1_ratio = gp[5], max_iter = gp[6])
	if model_str == "PER":  return Perceptron(penalty = gp[0], tol = gp[1], eta0 = gp[2], alpha = gp[3])
	if model_str == "RID":  return RidgeClassifier(alpha = gp[0], tol = gp[1], solver = gp[2])
	if model_str == "LDA":  return LinearDiscriminantAnalysis(solver = gp[0], tol = gp[1], shrinkage = gp[2])
	if model_str == "QDA":  return QuadraticDiscriminantAnalysis(tol = gp[0], reg_param = gp[1])
	if model_str == "SVC":  return SVC(C = gp[0], kernel = gp[1], degree = gp[2], gamma = gp[3], tol = gp[4])
	if model_str == "NSVC": return NuSVC(nu = gp[0], kernel = gp[1], degree = gp[2], gamma = gp[3], tol = gp[4])
	if model_str == "LSVC": return LinearSVC(penalty = gp[0], loss = gp[1], tol = gp[2], C = gp[3], max_iter = gp[4])
	if model_str == "KN":   return KNeighborsClassifier(n_neighbors = gp[0], weights = gp[1], algorithm = gp[2], leaf_size = gp[3], p = gp[4])
	if model_str == "RN":   return RadiusNeighborsClassifier(radius = gp[0], weights = gp[1], algorithm = gp[2], leaf_size = gp[3], p = gp[4], outlier_label = gp[5])
	if model_str == "NC":   return NearestCentroid(shrink_threshold = gp[0], metric = gp[1])
	if model_str == "NCA":  return Pipeline([('nca', NeighborhoodComponentsAnalysis(init = gp[0], tol = gp[1], max_iter = gp[2])), ('knn', KNeighborsClassifier(n_neighbors = gp[3], weights = gp[4], algorithm = gp[5], leaf_size = gp[6], p = gp[7]))])
	if model_str == "GP":   return GaussianProcessClassifier()
	if model_str == "GNB":  return GaussianNB(var_smoothing = gp[0])
	if model_str == "DT":   return DecisionTreeClassifier(criterion = gp[0], splitter = gp[1], min_samples_split = gp[2], min_samples_leaf = gp[3], max_features = gp[4])
	if model_str == "RF":   return RandomForestClassifier(n_estimators = gp[0], criterion = gp[1], min_samples_split = gp[2], min_samples_leaf = gp[3], max_features = gp[4])
	if model_str == "BAG":  return BaggingClassifier(n_estimators = gp[0], base_estimator = gp[1])
	if model_str == "ET":   return ExtraTreesClassifier(n_estimators = gp[0], criterion = gp[1], min_samples_split = gp[2], min_samples_leaf = gp[3], max_features = gp[4])
	if model_str == "AB":   return AdaBoostClassifier(base_estimator = gp[0], n_estimators = gp[1], algorithm = gp[2])
	if model_str == "HGB":  return HistGradientBoostingClassifier(loss = gp[0], max_leaf_nodes = gp[1])
	if model_str == "GB":   return GradientBoostingClassifier(loss = gp[0], n_estimators = gp[1], criterion = gp[2], min_samples_split = gp[3], min_samples_leaf = gp[4], max_features = gp[5])
	if model_str == "MLP":  return MLPClassifier(activation = gp[0], solver = gp[1], alpha = gp[2], learning_rate = gp[3], max_iter = gp[4])

def select_model(model, feature, cl, qos, run):
	with open(f"{gridsearch_dir}{run}{'_'.join([feature, str(cl), str(qos)])}.txt", 'r') as grid_fd:
		line = grid_fd.readline()
		while line:
			tokens = line.split('\t')
			if model == tokens[0]:
				gp = tokens[1:]
				while tokens[-1] != '\n':
					line = grid_fd.readline()
					tokens = line.split('\t')
				if gp[-1] != '\n':
					gp = [gp[0].split('(')[0] + '()'] + tokens[1:-2]
				else:
					gp = tokens[1:-2]
				break
			line = grid_fd.readline()
	gp_fixed = []
	for point in gp:
		if '.' in point or 'e-' in point: gp_fixed.append(float(point))
		elif all(c.isdigit() for c in point): gp_fixed.append(int(point))
		elif 'None' in point: gp_fixed.append(None)
		elif '(' in point:
			classifiers = {'SVC()': SVC(), 'SGDClassifier()': SGDClassifier(), 'KNeighborsClassifier()': KNeighborsClassifier(), \
						   'LogisticRegression()': LogisticRegression(), 'DecisionTree()': DecisionTreeClassifier(), \
						   'GaussianProcessClassifier()': GaussianProcessClassifier(), 'Perceptron()': Perceptron(), \
						   'RandomForestClassifier()': RandomForestClassifier(), 'GaussianNB()': GaussianNB()}
			gp_fixed.append(classifiers[point])
		else: gp_fixed.append(point)
	return model_library(model, gp_fixed)

#-------------------- Tools --------------------

temp_dir = '/home/ypap/temp/'

def pred_set_writer(measures, sets, data_name):
	def write_set(measures, classes, benches, name):
		fd = open(temp_dir + name + '.csv', mode='w')
		writer = csv.writer(fd, delimiter=',')
		writer.writerow(measures['Title'])
		for bench in benches:
			if bench in measures and bench in classes:
				writer.writerow(measures[bench] + [classes[bench]])
		fd.close()
	for (i, (pred_set, pred_class)) in enumerate(sets):
		write_set(measures, pred_class, pred_set, data_name + str(i))

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

def get_data_name(feature, cl, mod, qos, func):
	if type(mod) == str:
		return feature + str(cl) + mod + str(qos) + func
	modd = str(type(mod)).split('.')[-1].split("'")[0]
	return feature + str(cl) + modd + str(qos) + func

def run_model(answers, feature, cl, qos, model, func):
	start_train = time.perf_counter()
	train_data = pd.read_csv(temp_dir + get_data_name(feature, cl, model, qos, func) + '0.csv')
	test_data = pd.read_csv(temp_dir + get_data_name(feature, cl, model, qos, func) + '1.csv')

	if feature == 'cont': remove_cols = [0, 2, 3, 5, 6, 8, 16, 17, 19, 20, 22, 29]
	if feature == 'sens': remove_cols = [0, 2, 3, 8, 16, 17, 22, 29]
#	if feature == 'cont': remove_cols = [0, 2, 3, 4, 5, 6, 8, 15,16,17,18,19,20,21,22,23,24,25,26,27,28,29]
#	if feature == 'sens': remove_cols = [0, 8, 13, 15,16,17,18,19,20,21,22,23,24,25,26,27,28,29]
	#remove_cols = [0, 8, 22, 29]
	train = train_data.drop(train_data.columns[remove_cols], axis = 1)
	test = test_data.drop(test_data.columns[remove_cols], axis = 1)

	try:
		scaler = preprocessing.StandardScaler().fit(train)
	except:
		return []

	train_names = train_data['Benchmark']
	test_names = test_data['Benchmark']
	y_train = train_data['Class']
	y_test = test_data['Class']

	train_scaled = scaler.transform(train)
	test_scaled = scaler.transform(test)
	try:
		model.fit(train_scaled, y_train)
	except ValueError:
		return 0
	end_train = time.perf_counter()
	test_pred = model.predict(test_scaled)
	end_test = time.perf_counter()
	#print(f"Training: {(end_train - start_train):.6f}, Testing: {(end_test - end_train):.6f}")
	acc_score = model.score(test_scaled, y_test)

	for i in range(len(test_names)):
		answers[test_names[i]] = (test_pred[i], y_test[i])
	metrics_ = metrics.classification_report(y_test, test_pred, digits = 4, zero_division = 0, output_dict = True)
	return (metrics_['accuracy'], metrics_['macro avg']['f1-score'])

def get_train_test(train, test = ''):
	train = [x for sublist in list(map(lambda x: benchmark_suites[x], train.split(','))) for x in sublist]
	if test != '':
		return (train, [x for sublist in list(map(lambda x: benchmark_suites[x], test.split(','))) for x in sublist])
	return (train, [])

def help_message(ex):
	print(f"Usage    : {ex} <function> <feature> <qos> <classes> <model> <train> <test>\n" + \
		  f"Function : {' | '.join(functions)}\nFeature  : {' | '.join(features)}\n" + \
		  f"QoS      : {' | '.join(map(str, qos_levels))}\n" + \
		  f"Classes  : {' | '.join(map(str, classes_))}\nModel    : {' | '.join(models)}\n" + \
		  f"Train    : {' | '.join(benchmark_suites.keys())}\n" + \
		  f"Test     : {' | '.join(benchmark_suites.keys())}")
	return 0

def arg_check(args):
	if len(args) < 7: sys.exit(help_message(args[0]))
	(func, feature, qos, class_num, model, train) = args[1:7]
	qos = float(qos)
	class_num = int(class_num)
	if func not in functions or feature not in features or \
	   qos not in qos_levels or class_num not in classes_ or \
	   model not in models or (func == 'test' and len(args) < 8):
		sys.exit(help_message(args[0]))
	test = '' if func != 'test' else args[7]
	return [func, feature, qos, class_num, model, train, test]
