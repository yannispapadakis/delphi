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

def svc_grid(feature, class_num, qos, fd):
	kernels = ['linear', 'poly', 'rbf', 'sigmoid']
	cs = range(1, 11)
	degrees = range(1,6)

	max_svc = (0, '')
	for grid_point in list(product(*[kernels, cs, degrees])):
		(kernel, c, degree) = grid_point
		# TODO insert mismatches
		model = SVC(C = c, kernel = kernel, degree = degree)
		acc = model_run(model, feature, class_num, qos)
		max_svc = writer(['SVC'] + list(grid_point) + [acc], max_svc, fd)
	return max_svc[1]

def dt_grid(feature, class_num, qos, fd):
	criteria = ['gini', 'entropy']
	splitters = ['best', 'random']
	min_s_splits = range(2, 11)
	min_s_leaves = range(2, 11)
	max_feats = [None, 'sqrt', 'log2']

	max_dt = (0, '')
	for grid_point in list(product(*[criteria, splitters, min_s_splits, min_s_leaves, max_feats])):
		(criterion, splitter, min_s_split, min_s_leaf, max_features) = grid_point
		# TODO insert mismatches
		model = DecisionTreeClassifier(criterion=criterion, splitter=splitter,
									   min_samples_split=min_s_split, min_samples_leaf=min_s_leaf,
									   max_features=max_features)
		acc = model_run(model, feature, class_num, qos)
		max_dt = writer(['DT'] + list(grid_point) + [acc], max_dt, fd)
	return max_dt[1]

def kn_grid(feature, class_num, qos, fd):
	n_neighs = range(2, 11)
	weights_ = ['distance', 'uniform']
	algorithms = ['ball_tree', 'kd_tree', 'brute']
	leaf_sizes = [5 * x for x in range(1, 7)]
	ps = range(1,4)

	max_kn = (0, '')
	for grid_point in list(product(*[n_neighs, weights_, algorithms, leaf_sizes, ps])):
		(n_neighbors, weights, algorithm, leaf_size, p) = grid_point
		# TODO insert mismatches
		model = KNeighborsClassifier(n_neighbors=n_neighbors, weights=weights,
									 algorithm=algorithm, leaf_size=leaf_size, p=p)
		acc = model_run(model, feature, class_num, qos)
		max_kn = writer(['KN'] + list(grid_point) + [acc], max_kn, fd)
	return max_kn[1]

def rf_grid(feature, class_num, qos, fd):
	n_estimators_ = [5 * x for x in range(1,21)]
	criteria = ['entropy', 'gini']
	min_s_splits = range(2,11)
	min_s_leaves = range(2,11)
	max_feats = [None, 'sqrt', 'log2']
	bootstraps = [False, True]

	max_rf = (0, '')
	for grid_point in list(product(*[n_estimators_, criteria, min_s_splits, min_s_leaves, max_feats, bootstraps])):
		(n_estimators, criterion, min_s_split, min_s_leaf, max_features, bootstrap) = grid_point
		# TODO insert mismatches
		model = RandomForestClassifier(n_estimators=n_estimators, criterion=criterion, 
									   min_samples_split=min_s_split, min_samples_leaf=min_s_leaf,
									   max_features=max_features, bootstrap=bootstrap)
		acc = model_run(model, feature, class_num, qos)
		max_rf = writer(['RF'] + list(grid_point) + [acc], max_rf, fd)
	return max_rf[1]

def grid_search(args):
	if len(args) < 2: sys.exit(help_message(args))
	model = args[1]
	qos = float(args[2])
	feature = args[3]
	class_num = int(args[4])
	fd = open('_'.join([feature, str(class_num), str(qos), "search.txt"]), 'w')
	optimal = []

	fd_m = open('_'.join([model, str(qos), feature, str(class_num) + '.csv']), 'w')
	if model == 'SVC' or model == 'all':
		optimal.append(svc_grid(feature, class_num, qos, fd_m))
	if model == 'DT' or model == 'all':
		optimal.append(dt_grid(feature, class_num, qos, fd_m))
	if model == 'KN' or model == 'all':
		optimal.append(kn_grid(feature, class_num, qos, fd_m))
	if model == 'RF' or model == 'all':
		optimal.append(rf_grid(feature, class_num, qos, fd_m))
	for x in optimal:
		fd.write(x + '\n')
	fd_m.close()
	fd.close()
	return 0

def help_message(args):
	msg =  "Usage:   %s <model> <qos> <feature> <class_num>\n" % args[0]
	msg += "Model:   " + ' | '.join(models) + '\n'
	msg += "QoS:     " + ' | '.join(['1.1', '1.2', '1.3']) + '\n'
	msg += "Feature: " + ' | '.join(['sens', 'cont']) + '\n'
	msg += "Classes: " + ' | '.join(['2', '3']) + '\n'
	print(msg)
	return 0

if __name__ == '__main__':
	sys.exit(grid_search(sys.argv))
