import sys
sys.path.append('../')
from predictor import *

def model_run(model, feat, classes):
	acc = []
	for i in range(10):
		acc.append(predict(clos = [1.2], mod = model, feature = feat, class_num = classes))
	return np.mean(acc)

def writer(config, max_acc, fd):
	acc = config[-1]
	config = map(str, config)
	config = ''.join([it for sublist in zip(config, ['\t' for i in range(len(config))]) for it in sublist])
	fd.write(config + '\n')
	print(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\t' + config)
	return (acc, config) if acc > max_acc[0] else max_acc

def svc_grid(fd, feat, cl):
	svc_kernels = ['linear', 'poly', 'rbf', 'sigmoid']
	svc_c = range(1,11)
	svc_degrees = range(1,6)

	max_svc = (0, '')
	for kernel in svc_kernels:
		for C in svc_c:
			degrees = [3]
			if kernel == 'poly': degrees = svc_degrees
			for degree in degrees:
				model = SVC(C=C, kernel=kernel, degree=degree)
				acc = model_run(model, feat, cl)
				max_svc = writer(['SVC', C, kernel, degree, acc], max_svc, fd)
	return max_svc[1]

def dt_grid(fd, feat, cl):
	dt_criterion = ['gini', 'entropy']
	dt_splitter = ['best', 'random']
	dt_min_samples_split = range(2, 11)
	dt_min_samples_leaf = range(2, 11)
	dt_max_features = [None, 'sqrt', 'log2']

	max_dt = (0, '')
	for criterion in dt_criterion:
		for splitter in dt_splitter:
			for min_samples_split in dt_min_samples_split:
				for min_samples_leaf in dt_min_samples_leaf:
					for max_features in dt_max_features:
						model = DecisionTreeClassifier(criterion=criterion, splitter=splitter,
													   min_samples_split=min_samples_split,
													   min_samples_leaf=min_samples_leaf,
													   max_features=max_features)
						acc = model_run(model, feat, cl)
						max_dt = writer(['DT', criterion, splitter, min_samples_split, min_samples_leaf, max_features, acc], max_dt, fd)
	return max_dt[1]

def kn_grid(fd, feat, cl):
	kn_n_neighbors = range(2, 11)
	kn_weights = ['distance', 'uniform']
	kn_algorithm = ['ball_tree', 'kd_tree', 'brute']
	kn_leaf_size = [5 * x for x in range(1, 7)]
	kn_p = range(1,4)

	max_kn = (0, '')
	for n_neighbors in kn_n_neighbors:
		for weights in kn_weights:
			for algorithm in kn_algorithm:
				for leaf_size in kn_leaf_size:
					for p in kn_p:
						model = KNeighborsClassifier(n_neighbors=n_neighbors, weights=weights,
													 algorithm=algorithm, leaf_size=leaf_size, p=p)
						acc = model_run(model, feat, cl)
						max_kn = writer(['KN', n_neighbors, weights, algorithm, leaf_size, p, acc], max_kn, fd)
	return max_kn[1]

def rf_grid(fd, feat, cl):
	rf_n_estimators = [5 * x for x in range(1,21)]
	rf_criterion = ['entropy', 'gini']
	rf_min_samples_split = range(2,11)
	rf_min_samples_leaf = range(2,11)
	rf_max_features = [None, 'sqrt', 'log2']
	rf_bootstrap = [False, True]

	max_rf = (0, '')
	for n_estimators in rf_n_estimators:
		for criterion in rf_criterion:
			for min_samples_split in rf_min_samples_split:
				for min_samples_leaf in rf_min_samples_leaf:
					for max_features in rf_max_features:
						for bootstrap in rf_bootstrap:
							model = RandomForestClassifier(n_estimators=n_estimators, criterion=criterion, 
														   min_samples_split=min_samples_split,
														   min_samples_leaf=min_samples_leaf,
														   max_features=max_features, bootstrap=bootstrap)
							acc = model_run(model, feat, cl)
							max_rf = writer(['RF', n_estimators, criterion, min_samples_split, min_samples_leaf, max_features, bootstrap, acc], max_rf, fd)
	return max_rf[1]

def grid_search(args):
	m = args[1]
	feat = args[2]
	cl = int(args[3])
	fd = open(feat + str(cl) + "_search.txt", 'w')
	optimal = []

	if m == 'SVC' or m == 'all':
		fd1 = open(feat + str(cl) + '_SVC.csv', 'w')
		optimal.append(svc_grid(fd1, feat, cl))
		fd1.close()
	if m == 'DT' or m == 'all':
		fd2 = open(feat + str(cl) + '_DT.csv', 'w')
		optimal.append(dt_grid(fd2, feat, cl))
		fd2.close()
	if m == 'KN' or m == 'all':
		fd3 = open(feat + str(cl) + '_KN.csv', 'w')
		optimal.append(kn_grid(fd3, feat, cl))
		fd3.close()
	if m == 'RF' or m == 'all':
		fd4 = open(feat + str(cl) + '_RF.csv', 'w')
		optimal.append(rf_grid(fd4, feat, cl))
		fd4.close()
	for x in optimal:
		fd.write(x + '\n')
	fd.close()
	return 0

if __name__ == '__main__':
	sys.exit(grid_search(sys.argv))
