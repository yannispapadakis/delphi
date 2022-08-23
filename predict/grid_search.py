#!/usr/bin/python3
import sys
from itertools import product
from predictor import *

def model_run(model, feature, class_num, qos):
	acc = []
	for i in range(10):
		acc.append(prediction(['cv', feature, qos, class_num, model]))
	return np.mean(acc)

def writer(config, max_acc, fd):
	acc = config[-1]
	config = list(map(str, config))
	config = ''.join([it for sublist in zip(config, ['\t' for i in range(len(config))]) for it in sublist])
	fd.write(config + '\n')
	print(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\t' + config)
	return (acc, config) if acc > max_acc[0] else max_acc

def lr_grid(feature, class_num, qos, fd):
	penalties = ['l1', 'l2', 'elasticnet', 'none']
	tolerance = [1e-3, 1e-4, 1e-5]
	cs = map(lambda x: 10 ** x, range(-1, 2))
	solvers = ['newton-cg', 'lbfgs', 'liblinear', 'sag', 'saga']
	l1_ratios = [0.25, 0.5, 0.75]
	max_iters = [10000]

	search_space = [penalties, tolerance, cs, solvers, l1_ratios, max_iters]
	def mismatch(grid_point):
		(penalty, _, c, solver, l1_ratio, max_iter) = grid_point
		return (solver in ['newton-cg', 'lbfgs', 'sag'] and penalty in ['l1', 'elasticnet'] or \
				solver == 'liblinear' and penalty in ['none', 'elasticnet'] or \
				penalty in ['l1', 'l2', 'none'] and l1_ratio > 0.0 or \
				penalty == 'elasticnet' and l1_ratio < 1e-3 or \
				penalty == 'none' and c > 0.5)
	return grid_run('LR', search_space, mismatch, feature, class_num, qos, fd)

def sgd_grid(feature, class_num, qos, fd):
	losses = ['hinge', 'log', 'modified_huber', 'squared_hinge', 'perceptron']
	penalties = ['l2', 'l1', 'elasticnet']
	alphas = map(lambda x: 10 ** (-x), range(3, 6))
	learning_rates = ['constant', 'optimal', 'invscaling', 'adaptive']
	etas = [0.0, 1e-2, 1e-1, 1.0]
	l1_ratios = [0.25, 0.5, 0.75]
	max_iters = [10000]

	search_space = [losses, penalties, alphas, learning_rates, etas, l1_ratios, max_iters]
	def mismatch(grid_point):
		(_, penalty, _, learning_rate, eta, l1_ratio, _) = grid_point
		return (learning_rate == 'optimal' and eta > 1e-3 or \
				learning_rate != 'optimal' and eta < 1e-5 or \
				penalty != 'elasticnet' and l1_ratio > 0.25)
	return grid_run('SGD', search_space, mismatch, feature, class_num, qos, fd)

def pa_grid(feature, class_num, qos, fd):
	cs = map(lambda x: 10 ** x, range(-1, 2))
	tolerance = [1e-4, 1e-3, None]
	losses = ['hinge', 'squared_hinge']
	search_space = [cs, tolerance, losses]
	return grid_run('PA', search_space, lambda x: False, feature, class_num, qos, fd)

def per_grid(feature, class_num, qos, fd):
	penalties = ['l1', 'l2', 'elasticnet', None]
	tolerance = [1e-3, 1e-4, 1e-5]
	etas = [0.1, 1.0, 10.0]
	alphas = map(lambda x: 10 ** (-x), range(2, 5))
	search_space = [penalties, tolerance, etas, alphas]
	return grid_run("PER", search_space, lambda x: False, feature, class_num, qos, fd)

def rid_grid(feature, class_num, qos, fd):
	alphas = [0.01, 0.1, 1.0, 10.0]
	tolerance = [1e-3, 1e-4, 1e-5]
	solvers = ['auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg', 'sag', 'saga', 'lbfgs']
	search_space = [alphas, tolerance, solvers]
	return grid_run("RID", search_space, lambda x: False, feature, class_num, qos, fd)

def lda_grid(feature, class_num, qos, fd):
	solvers = ['svd', 'lsqr', 'eigen']
	shrinkages = [None, 'auto', 0.25, 0.5, 0.75]
	tolerance = [1e-3, 1e-4, 1e-5]

	search_space = [solvers, tolerance, shrinkages]
	def mismatch(grid_point):
		(solver, _, shrinkage) = grid_point
		return (solver == 'svd' and shrinkage != None)
	return grid_run("LDA", search_space, mismatch, feature, class_num, qos, fd)

def qda_grid(feature, class_num, qos, fd):
	tolerance = [1e-3, 1e-4, 1e-5]
	reg_param = [0.0, 0.01, 0.1, 1.0]
	search_space = [tolerance, reg_param]
	return grid_run("QDA", search_space, lambda x: False, feature, class_num, qos, fd)

def svc_grid(feature, class_num, qos, fd):
	cs = [0.1, 1.0, 10.0]
	kernels = ['linear', 'poly', 'rbf', 'sigmoid']
	degrees = range(1,6)
	gammas = ['scale', 'auto']
	tolerance = [1e-3, 1e-4, 1e-5]
	search_space = [cs, kernels, degrees, gammas, tolerance]
	return grid_run("SVC", search_space, lambda x: False, feature, class_num, qos, fd)

def nsvc_grid(feature, class_num, qos, fd):
	nus = [0.01, 0.1, 1.0]
	kernels = ['linear', 'poly', 'rbf', 'sigmoid']
	degrees = range(1,6)
	gammas = ['scale', 'auto']
	tolerance = [1e-3, 1e-4, 1e-5]
	search_space = [nus, kernels, degrees, gammas, tolerance]
	return grid_run("NSVC", search_space, lambda x: False, feature, class_num, qos, fd)

def lsvc_grid(feature, class_num, qos, fd):
	penalties = ['l1', 'l2']
	losses = ['hinge', 'squared_hinge']
	tolerance = [1e-3, 1e-4, 1e-5]
	cs = [0.1, 1.0, 10.0]
	max_iters = [100000]

	search_space = [penalties, losses, tolerance, cs, max_iters]
	def mismatch(grid_point):
		(penalty, loss, _, _, _) = grid_point
		return (penalty == 'l1' and loss == 'hinge')
	return grid_run("LSVC", search_space, mismatch, feature, class_num, qos, fd)

def kn_grid(feature, class_num, qos, fd):
	n_neighs = [2, 5, 8, 10]
	weights_ = ['distance', 'uniform']
	algorithms = ['ball_tree', 'kd_tree', 'brute']
	leaf_sizes = [15, 30, 45]
	ps = [1, 2, 3]
	search_space = [n_neighs, weights_, algorithms, leaf_sizes, ps]
	return grid_run("KN", search_space, lambda x: False, feature, class_num, qos, fd)

def rn_grid(feature, class_num, qos, fd):
	radiuses = [1.0, 5.0, 10.0, 20.0]
	weights = ['uniform', 'distance']
	algorithms = ['ball_tree', 'kd_tree', 'brute']
	leaf_sizes = [15, 30, 45]
	ps = [1, 2, 3]
	label = ['most_frequent']
	search_space = [radiuses, weights, algorithms, leaf_sizes, ps, label]
	return grid_run("RN", search_space, lambda x: False, feature, class_num, qos, fd)

def nc_grid(feature, class_num, qos, fd):
	metrics = ["euclidean", "manhattan"]
	shrink_threshold = [0.1, 1.0, None]
	search_space = [shrink_threshold, metrics]
	return grid_run("NC", search_space, lambda x: False, feature, class_num, qos, fd)

def gp_grid(feature, class_num, qos, fd):
	search_space = []
	return grid_run("GP", search_space, lambda x: False, feature, class_num, qos, fd)

def gnb_grid(feature, class_num, qos, fd):
	var_smoothing = [1e-8, 1e-9, 1e-10]
	search_space = [var_smoothing]
	return grid_run("GNB", search_space, lambda x: False, feature, class_num, qos, fd)

def dt_grid(feature, class_num, qos, fd):
	criteria = ['gini', 'entropy']
	splitters = ['best', 'random']
	min_s_splits = [2, 4, 8, 16]
	min_s_leaves = [1, 2, 4, 8]
	max_feats = [None, 'sqrt', 'log2']
	search_space = [criteria, splitters, min_s_splits, min_s_leaves, max_feats]
	return grid_run("DT", search_space, lambda x: False, feature, class_num, qos, fd)

def rf_grid(feature, class_num, qos, fd):
	n_estimators = [10, 30, 50, 75, 100]
	criteria = ['entropy', 'gini']
	min_s_splits = [2, 4, 8, 16]
	min_s_leaves = [1, 2, 4, 8]
	max_feats = [None, 'sqrt', 'log2']
	search_space = [n_estimators, criteria, min_s_splits, min_s_leaves, max_feats]
	return grid_run("RF", search_space, lambda x: False, feature, class_num, qos, fd)

def bag_grid(feature, class_num, qos, fd):
	n_estimators = [10, 30, 50, 75, 100]
	base_estimator = [SVC(), SGDClassifier(), KNeighborsClassifier(), LogisticRegression(), None, GaussianProcessClassifier(), Perceptron(), RandomForestClassifier()]
	search_space = [n_estimators, base_estimator]
	return grid_run("BAG", search_space, lambda x: False, feature, class_num, qos, fd)

def et_grid(feature, class_num, qos, fd):
	n_estimators = [10, 30, 50, 75, 100]
	criterion = ['gini', 'entropy']
	min_samples_split = [2, 4, 8, 16]
	min_samples_leaf = [1, 2, 4, 8]
	max_features = ['sqrt', 'log2', None]
	search_space = [n_estimators, criterion, min_samples_split, min_samples_leaf, max_features]
	return grid_run("ET", search_space, lambda x: False, feature, class_num, qos, fd)

def ab_grid(feature, class_num, qos, fd):
	base_estimator = [SVC(), SGDClassifier(), KNeighborsClassifier(), LogisticRegression(), None, GaussianProcessClassifier(), GaussianNB(), Perceptron(), RandomForestClassifier()]
	n_estimators = [10, 30, 50, 75, 100]
	algorithms = ['SAMME']
	search_space = [base_estimator, n_estimators, algorithms]
	return grid_run("AB", search_space, lambda x: False, feature, class_num, qos, fd)

def hgb_grid(feature, class_num, qos, fd):
	loss = ['log_loss', 'auto', 'binary_crossentropy', 'categorical_crossentropy']
	max_leaf_nodes = [2, 8, 16, 32, None]
	search_space = [loss, max_leaf_nodes]
	return grid_run("HGB", search_space, lambda x: False, feature, class_num, qos, fd)

def gb_grid(feature, class_num, qos, fd):
	loss = ['deviance', 'exponential']
	n_estimators = [10, 30, 50, 75, 100]
	criterion = ['friedman_mse', 'mse', 'mae']
	min_samples_split = [2, 4, 8, 16]
	min_samples_leaf = [1, 2, 4, 8]
	max_features = ['sqrt', 'log2']
	search_space = [loss, n_estimators, criterion, min_samples_split, min_samples_leaf, max_features]
	return grid_run("GB", search_space, lambda x: False, feature, class_num, qos, fd)

def mlp_grid(feature, class_num, qos, fd):
	activation = ['identity', 'logistic', 'tanh', 'relu']
	solver = ['lbfgs', 'sgd', 'adam']
	alpha = [1e-3, 1e-4, 1e-5]
	learning_rate = ['constant', 'invscaling', 'adaptive']
	max_iter = [10000]
	search_space = [activation, solver, alpha, learning_rate, max_iter]
	return grid_run("MLP", search_space, lambda x: False, feature, class_num, qos, fd)

def grid_run(model_str, search_space, mismatch, feature, class_num, qos, fd):
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

	max_acc = (0, "")
	for grid_point in list(product(*search_space)):
		if mismatch(grid_point): continue
		model = model_library(model_str, grid_point)
		acc = model_run(model, feature, class_num, qos)
		max_acc = writer([model_str] + list(grid_point) + [acc], max_acc, fd)
	return max_acc[1]

grid_methods = {'LR': lr_grid, 'PA': pa_grid, 'SGD': sgd_grid, 'PER': per_grid, 'RID': rid_grid, \
				'LDA': lda_grid, 'QDA': qda_grid, 'SVC': svc_grid, 'NSVC': nsvc_grid, 'LSVC': lsvc_grid, \
				'KN': kn_grid, 'RN': rn_grid, 'NC': nc_grid, 'GP': gp_grid, 'GNB': gnb_grid, 'DT': dt_grid, \
				'RF': rf_grid, 'BAG': bag_grid, 'ET': et_grid, 'AB': ab_grid, 'HGB': hgb_grid, 'GB': gb_grid, 'MLP': mlp_grid}

def grid_search(args):
	if len(args) < 2: sys.exit(help_message(args))
	grid_models = args[1].split(',')
	if grid_models[0] == 'all': grid_models = models
	qos = float(args[2])
	feature = args[3]
	class_num = int(args[4])
	fd_acc = open(csv_dir + 'GridSearch/' + '_'.join([feature, str(class_num), str(qos), ".txt"]), 'w')
	fd_det = open(csv_dir + 'GridSearch/' + '_'.join(feature, str(class_num), str(qos) + '.csv']), 'a')
	optimal = []

	for model in grid_models:
		optimal.append(grid_methods[model](feature, class_num, qos, fd_det))
	for x in optimal:
		fd_acc.write(x + '\n')
	fd_acc.close()
	fd_det.close()

def help_message(args):
	print("Usage:   %s <models> <qos> <feature> <class_num>\n" % args[0] + \
		  "Models:  " + ' | '.join(models + ['all']) + '\n' + \
		  "QoS:     " + ' | '.join(['1.1', '1.2', '1.3']) + '\n' + \
		  "Feature: " + ' | '.join(['sens', 'cont']) + '\n' + \
		  "Classes: " + ' | '.join(['2', '3']) + '\n')
	return 0

if __name__ == '__main__':
	grid_search(sys.argv)
