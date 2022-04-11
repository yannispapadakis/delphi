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
	cs = map(float, range(1, 4))
	solvers = ['newton-cg', 'lbfgs', 'liblinear', 'sag', 'saga']

	search_space = [penalties, tolerance, cs, solvers]
	def mismatch(grid_point):
		(penalty, _, _, solver) = grid_point
		return (solver in ['newton-cg', 'lbfgs', 'sag'] and penalty in ['l1', 'elasticnet'] or \
				solver == 'liblinear' and penalty in ['none', 'elasticnet'])
	return grid_run('LR', search_space, mismatch, feature, class_num, qos, fd)

def sgd_grid(feature, class_num, qos, fd):
	losses = ['hinge', 'log', 'modified_huber', 'squared_hinge', 'perceptron']
	penalties = ['l2', 'l1', 'elasticnet']
	alphas = [1e-2, 1e-3, 1e-4]
	learning_rates = ['constant', 'optimal', 'invscaling', 'adaptive']
	etas = [1e-2, 1e-1, 0.0, 1.0, 10.0]

	search_space = [losses, penalties, alphas, learning_rates, etas]
	def mismatch(grid_point):
		(_, _, _, learning_rate, eta) = grid_point
		return ((learning_rate != 'optimal' and eta < 1e-5) or \
				(learning_rate == 'optimal' and eta > 1e-5))
	return grid_run('SGD', search_space, mismatch, feature, class_num, qos, fd)

def pa_grid(feature, class_num, qos, fd):
	cs = [0.1, 0.5, 1.0, 5.0, 10.0]
	tolerance = [1e-4, 1e-3, None]
	losses = ['hinge', 'squared_hinge']
	search_space = [cs, tolerance, losses]
	return grid_run('PA', search_space, lambda x: False, feature, class_num, qos, fd)

def per_grid(feature, class_num, qos, fd):
	penalties = ['l1', 'l2', 'elasticnet', None]
	tolerance = [1e-3, 1e-4, 1e-5]
	search_space = [penalties, tolerance]
	return grid_run("PER", search_space, lambda x: False, feature, class_num, qos, fd)

def rid_grid(feature, class_num, qos, fd):
	alphas = [0.01, 0.1, 1.0, 10.0]
	tolerance = [1e-3, 1e-4, 1e-5]
	solvers = ['auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg', 'sag', 'saga', 'lbfgs']
	search_space = [alphas, tolerance, solvers]
	return grid_run("RID", search_space, lambda x: False, feature, class_num, qos, fd)

def lda_grid(feature, class_num, qos, fd):
	solvers = ['svd', 'lsqr', 'eigen']
	tolerance = [1e-3, 1e-4, 1e-5]
	search_space = [solvers, tolerance]
	return grid_run("LDA", search_space, lambda x: False, feature, class_num, qos, fd)

def qda_grid(feature, class_num, qos, fd):
	tolerance = [1e-3, 1e-4, 1e-5]
	search_space = [tolerance]
	return grid_run("QDA", search_space, lambda x: False, feature, class_num, qos, fd)

def svc_grid(feature, class_num, qos, fd):
	cs = [0.1, 0.5, 1.0, 5.0, 10.0]
	kernels = ['linear', 'poly', 'rbf', 'sigmoid']
	degrees = range(1,6)
	gammas = ['scale', 'auto']
	tolerance = [1e-3, 1e-4, 1e-5]
	search_space = [cs, kernels, degrees, gammas, tolerance]
	return grid_run("SVC", search_space, lambda x: False, feature, class_num, qos, fd)

def nsvc_grid(feature, class_num, qos, fd):
	nus = [0.01, 0.1, 0.5, 1.0]
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
	cs = [0.1, 0.5, 1.0, 5.0, 10.0]

	search_space = [penalties, losses, tolerance, cs]
	def mismatch(grid_point):
		(penalty, loss, _, _) = grid_point
		return (penalty == 'l1' and loss == 'hinge')
	return grid_run("LSVC", search_space, mismatch, feature, class_num, qos, fd)

def kn_grid(feature, class_num, qos, fd):
	n_neighs = [2, 5, 8, 10]
	weights_ = ['distance', 'uniform']
	algorithms = ['ball_tree', 'kd_tree', 'brute']
	leaf_sizes = [15, 30, 45]
	ps = range(1,4)
	search_space = [n_neighs, weights_, algorithms, leaf_sizes, ps]
	return grid_run("LSVC", search_space, lambda x: False, feature, class_num, qos, fd)

def rn_grid(feature, class_num, qos, fd):
	radiuses = [0.1, 0.5, 1.0, 5.0, 10.0]
	weights = ['uniform', 'distance']
	algorithms = ['ball_tree', 'kd_tree', 'brute']
	leaf_sizes = [15, 30, 45]
	ps = [1, 2, 3]
	search_space = [radiuses, weights, algorithms, leaf_sizes, ps]
	return grid_run("RN", search_space, lambda x: False, feature, class_num, qos, fd)

def nc_grid(feature, class_num, qos, fd):
	shrink_threshold = [0.1, 1.0, None]
	search_space = [shrink_threshold]
	return grid_run("NC", search_space, lambda x: False, feature, class_num, qos, fd)

def gp_grid(feature, class_num, qos, fd):
	search_space = []
	return grid_run("GP", search_space, lambda x: False, feature, class_num, qos, fd)

def gnb_grid(feature, class_num, qos, fd):
	search_space = []
	return grid_run("GNB", search_space, lambda x: False, feature, class_num, qos, fd)

def mnb_grid(feature, class_num, qos, fd):
	alpha = [0.0, 0.1, 1.0, 10.0]
	search_space = [alpha]
	return grid_run("MNB", search_space, lambda x: False, feature, class_num, qos, fd)

def dt_grid(feature, class_num, qos, fd):
	criteria = ['gini', 'entropy']
	splitters = ['best', 'random']
	min_s_splits = [2, 4, 8, 16]
	min_s_leaves = [1, 2, 4, 8]
	max_feats = [None, 'sqrt', 'log2']
	search_space = [criteria, splitters, min_s_splits, min_s_leaves, max_feats]
	return grid_run("DT", search_space, lambda x: False, feature, class_num, qos, fd)

def rf_grid(feature, class_num, qos, fd):
	n_estimators_ = [10, 30, 50, 75, 100]
	criteria = ['entropy', 'gini']
	min_s_splits = [2, 4, 8, 16]
	min_s_leaves = [1, 2, 4, 8]
	max_feats = [None, 'sqrt', 'log2']
	search_space = [n_estimators, criteria, min_s_splits, min_s_leaves, max_feats]
	return grid_run("RF", search_space, lambda x: False, feature, class_num, qos, fd)

def bag_grid(feature, class_num, qos, fd):
	n_estimators = [10, 30, 50, 75, 100]
	base_estimator = [SVC(), SGDClassifier(), KNeighborsClassifier(), LogisticRegression(), None]
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
	base_estimator = [SVC(), SGDClassifier(), KNeighborsClassifier(), LogisticRegression(), None]
	n_estimators = [10, 30, 50, 75, 100]
	search_space = [base_estimator, n_estimators]
	return grid_run("AB", search_space, lambda x: False, feature, class_num, qos, fd)

def hgb_grid(feature, class_num, qos, fd):
	loss = ['binary_crossentropy', 'categorical_crossentropy']
	max_leaf_nodes = [2, 8, 16, 31, None]
	search_space = [loss, max_leaf_nodes]
	return grid_run("HGB", search_space, lambda x: False, feature, class_num, qos, fd)

def gb_grid(feature, class_num, qos, fd):
	loss = ['deviance', 'exponential']
	n_estimators = [10, 30, 50, 75, 100]
	criterion = ['friedman_mse', 'squared_error', 'mse', 'mae']
	min_samples_split = [2, 4, 8, 16]
	min_samples_leaf = [1, 2, 4, 8]
	max_features = ['sqrt', 'log2']
	search_space = [loss, n_estimators, criterion, min_samples_split, min_samples_leaf, max_features]
	return grid_run("GB", search_space, lambda x: False, feature, class_num, qos, fd)

def vot_grid(feature, class_num, qos, fd):
	voting = ['hard', 'soft']
	search_space = [voting]
	return grid_run("VOT", search_space, lambda x: False, feature, class_num, qos, fd)

def mlp_grid(feature, class_num, qos, fd):
	activation = ['identity', 'logistic', 'tanh', 'relu']
	solver = ['lbfgs', 'sgd', 'adam']
	alpha = [1e-3, 1e-4, 1e-5]
	learning_rate = ['constant', 'invscaling', 'adaptive']
	search_space = [activation, solver, alpha, learning_rate]
	return grid_run("MLP", search_space, lambda x: False, feature, class_num, qos, fd)

def grid_run(model_str, search_space, mismatch, feature, class_num, qos, fd):
	def model_library(model_str, gp):
		if model_str == "LR":   return LogisticRegression(penalty = gp[0], tol = gp[1], C = gp[2], solver = gp[3])
		if model_str == "PA":   return PassiveAggressiveClassifier(C = gp[0], tol = gp[1], loss = gp[2])
		if model_str == "SGD":  return SGDClassifier(loss = gp[0], penalty = gp[1], alpha = gp[2], learning_rate = gp[3], eta0 = gp[4])
		if model_str == "PER":  return Perceptron(penalty = gp[0], tol = gp[1])
		if model_str == "RID":  return RidgeClassifier(alpha = gp[0], tol = gp[1], solver = gp[2])
		if model_str == "LDA":  return LinearDiscriminantAnalysis(solver = gp[0], tol = gp[1])
		if model_str == "QDA":  return QuadraticDiscriminantAnalysis(tol = gp[0])
		if model_str == "SVC":  return SVC(C = gp[0], kernel = gp[1], degree = gp[2], gamma = gp[3], tol = gp[4])
		if model_str == "NSVC": return NuSVC(nu = gp[0], kernel = gp[1], degree = gp[2], gamma = gp[3], tol = gp[4])
		if model_str == "LSVC": return LinearSVC(penalty = gp[0], loss = gp[1], tol = gp[2], C = gp[3])
		if model_str == "KN":   return KNeighborsClassifier(n_neighbors = gp[0], weights = gp[1], algorithm = gp[2], leaf_size = gp[3], p = gp[4])
		if model_str == "RN":   return RadiusNeighborsClassifier(radius = gp[0], weights = gp[1], algorithm = gp[2], leaf_size = gp[3], p = gp[4])
		if model_str == "NC":   return NearestCentroid(shrink_threshold = gp[0])
		if model_str == "GP":   return GaussianProcessClassifier()
		if model_str == "GNB":  return GaussianNB()
		if model_str == "MNB":  return MultinomialNB(alpha = gp[0])
		if model_str == "DT":   return DecisionTreeClassifier(criterion = gp[0], splitter = gp[1], min_samples_split = gp[2], min_samples_leaf = gp[3], max_features = gp[4])
		if model_str == "RF":   return RandomForestClassifier(n_estimators = gp[0], criterion = gp[1], min_samples_split = gp[2], min_samples_leaf = gp[3], max_features = gp[4])
		if model_str == "BAG":  return BaggingClassifier(n_estimators = gp[0], base_estimator = gp[1])
		if model_str == "ET":   return ExtraTreesClassifier(n_estimators = gp[0], criterion = gp[1], min_samples_split = gp[2], min_samples_leaf = gp[3], max_features = gp[4])
		if model_str == "AB":   return AdaBoostClassifier(base_estimator = gp[0], n_estimators = gp[1])
		if model_str == "HGB":  return HistGradientBoostingClassifier(loss = gp[0], max_leaf_nodes = gp[1])
		if model_str == "GB":   return GradientBoostingClassifier(loss = gp[0], n_estimators = gp[1], criterion = gp[2], min_samples_split = gp[3], min_samples_leaf = gp[4], max_features = gp[5])
		if model_str == "VOT":  return VotingClassifier(voting = gp[0])
		if model_str == "MLP":  return MLPClassifier(activation = gp[0], solver = gp[1], alpha = gp[2], learning_rate = gp[3])

	max_acc = (0, "")
	for grid_point in list(product(*search_space)):
		if mismatch(grid_point): continue
		model = model_library(model_str, grid_point)
		acc = model_run(model_str, feature, class_num, qos)
		max_acc = writer([model_str] + list(grid_point) + [acc], max_acc, fd)
	return max_acc[1]

grid_methods = {'LR': lr_grid, 'PA': pa_grid, 'SGD': sgd_grid, 'PER': per_grid, 'RID': rid_grid, \
				'LDA': lda_grid, 'QDA': qda_grid, 'SVC': svc_grid, 'NSVC': nsvc_grid, 'LSVC': lsvc_grid, \
				'KN': kn_grid, 'RN': rn_grid, 'NC': nc_grid, 'GP': gp_grid, 'GNB': gnb_grid, 'MNB': mnb_grid, \
				'DT': dt_grid, 'RF': rf_grid, 'AB': ab_grid, 'HGB': hgb_grid, 'VOT': vot_grid}

def grid_search(args):
	if len(args) < 2: sys.exit(help_message(args))
	grid_models = args[1].split(',')
	if grid_models[0] == 'all': grid_models = models
	qos = float(args[2])
	feature = args[3]
	class_num = int(args[4])
	fd = open('_'.join([feature, str(class_num), str(qos), "search.txt"]), 'w')
	optimal = []

	for model in grid_models:
		fd_m = open('_'.join([model, str(qos), feature, str(class_num) + '.csv']), 'w')
		optimal.append(grid_methods[model](feature, class_num, qos, fd_m))
		fd_m.close()
	for x in optimal:
		fd.write(x + '\n')
	fd.close()
	return 0

def help_message(args):
	msg =  "Usage:   %s <models> <qos> <feature> <class_num>\n" % args[0]
	msg += "Models:  " + ' | '.join(models + ['all']) + '\n'
	msg += "QoS:     " + ' | '.join(['1.1', '1.2', '1.3']) + '\n'
	msg += "Feature: " + ' | '.join(['sens', 'cont']) + '\n'
	msg += "Classes: " + ' | '.join(['2', '3']) + '\n'
	print(msg)
	return 0

if __name__ == '__main__':
	sys.exit(grid_search(sys.argv))
