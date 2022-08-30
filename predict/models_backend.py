import sys
from sklearn.linear_model import LogisticRegression, SGDClassifier, PassiveAggressiveClassifier, Perceptron, RidgeClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.svm import SVC, NuSVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier, RadiusNeighborsClassifier, NearestCentroid
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.experimental import enable_hist_gradient_boosting
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier, ExtraTreesClassifier, AdaBoostClassifier, HistGradientBoostingClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier

qos_levels = [1 + 0.1 * x for x in range(1, 4)]
models = ['LR', 'SGD', 'PA', 'PER', 'RID', \
		  'LDA', 'QDA', 'SVC', 'NSVC', 'LSVC', \
		  'DT', 'KN', 'RN', 'NC', 'GP', 'GNB', \
		  'RF', 'BAG', 'ET', 'AB', 'HGB', 'GB', 'MLP']

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

def select_model(model, feature, cl, qos):
	run = 'spec/'
	grid_fd = open(csv_dir + "GridSearch/" + run + '_'.join([feature, str(cl), str(qos)]) + '.txt', 'r')
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

def get_data_name(feature, cl, mod, qos):
	if type(mod) == str:
		return feature + str(cl) + mod + str(qos)
	modd = str(type(mod)).split('.')[-1].split("'")[0]
	if modd == 'DecisionTreeClassifier': modd = 'DT'
	if modd == 'KNeighbors': modd = 'KN'
	if modd == 'RandomForest': modd = 'RF'
	return feature + str(cl) + modd + str(qos)

def run_model(answers, feature, cl, qos, mod):
	train_data = pd.read_csv(csv_dir + get_data_name(feature, cl, mod, qos) + 'train.csv')
	test_data = pd.read_csv(csv_dir + get_data_name(feature, cl, mod, qos) + 'test.csv')

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
	print("Usage:    %s <function> <feature> <qos> <classes> <model>\n" % ex + \
		  "Function: " + ' | '.join(['test', 'cv']) + '\n' + \
		  "Feature:  " + ' | '.join(['sens', 'cont']) + '\n' + \
		  "QoS:      " + ' | '.join(map(str, qos_levels)) + "\n" + \
		  "Classes:  " + ' | '.join(map(str, [2, 3])) + '\n' + \
		  "Model:    " + ' | '.join(models))
	return 0

def arg_check(args):
	if len(args) < 6: sys.exit(help_message(args[0]))
	(func, feature, qos, class_num, model) = args[1:]
	qos = float(qos)
	class_num = int(class_num)
	if func not in ['cv', 'test'] or \
	   feature not in ['sens', 'cont'] or \
	   qos not in qos_levels or \
	   class_num not in [2, 3] or \
	   model not in models:
	   sys.exit(help_message(args[0]))
