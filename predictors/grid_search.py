from predictor import *

def model_run(model, feat):
	return 1
	acc = []
	for i in range(10):
		acc.append(predict(mod = model, feature = feat))
	return np.mean(acc)

def writer(config, max_acc, fd):
	acc = config[-1]
	config = map(str, config)
	config = [it for sublist in zip(config, ['\t' for i in range(len(config))]) for it in sublist]
	fd.write(''.join(config) + '\n')
	print(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + t + ''.join(config))
	return (acc, config) if acc > max_acc[0] else max_acc

def svc_grid(fd, feat):
	svc_kernels = ['linear', 'poly', 'rbf', 'sigmoid']
	svc_c = range(1,11)
	svc_degrees = range(1,5)

	max_svc = (0, '')
	for kernel in svc_kernels:
		for C in svc_c:
			degrees = [3]
			if kernel == 'poly': degrees = svc_degrees
			for degree in degrees:
				model = SVC(C=C, kernel=kernel, degree=degree)
				acc = model_run(model, feat)
				max_svc = writer(['SVC', C, kernel, degree, acc], max_svc, fd)
	return max_svc

def dt_grid(fd, feat):
	dt_criterion = ['gini', 'entropy']
	dt_splitter = ['best', 'random']
	dt_min_samples_split = range(1, 11)
	dt_min_samples_leaf = range(1, 11)
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
						acc = model_run(model, feat)
						max_dt = writer(['DT', criterion, splitter, min_samples_split, min_samples_leaf, max_features, acc], max_dt, fd)
	return max_dt

def kn_grid(fd, feat)
	kn_n_neighbors = range(2, 8)
	kn_weights = ['uniform', 'distance']:
	kn_algorithm = ['ball_tree', 'kd_tree', 'brute']
	kn_leaf_size = [5 * x for x in range(1, 5)]
	kn_p = range(1,4)

	max_kn = (0, '')
	for n_neighbors in kn_n_neighbors:
		for weights in kn_weights:
			for algorithm in kn_algorithm:
				for leaf_size in kn_leaf_size:
					for p in kn_p:
						model = KNeighborsClassifier(n_neighbors=n_neighbors, weights=weights,
													 algorithm=algorithm, leaf_size=leaf_size, p=p)
						acc = model_run(model, feat)
						max_kn = writer(['KN', n_neighbors, weights, algorithm, leaf_size, p, acc], max_kn, fd)
	return max_kn

def rf_grid(fd, feat):
	rf_n_estimators = [5 * x for x in range(4,11)]
	rf_criterion = ['gini', 'entropy']
	rf_min_samples_split = range(4,10)
	rf_min_samples_leaf = range(4,10)
	rf_max_features = [None, 'sqrt', 'log2']
	rf_bootstrap = [False, True]

	for n_estimators in rf_n_estimators:
		for criterion in rf_criterion:
			for min_samples_split in rf_min_samples_split:
				for min_samples_leaf in rf_min_samples_leaf:
					for max_features in rf_max_features:
						for bootstrap in rf_bootstrap::
							model = RandomForestClassifier(n_estimators=n_estimators, criterion=criterion, 
														   min_samples_split=min_samples_split,
														   min_samples_leaf=min_samples_leaf,
														   max_features=max_features, bootstrap=bootstrap)
							acc = model_run(model, feat)
							max_rf = writer(['RF', n_estimators, criterion, min_samples_split, min_samples_leaf, max_features, bootstrap, acc], max_rf, fd)
	return max_rf

def grid_search(m):
	fd = open("t_search.txt", 'w')
	max_dt = max_kn = max_rf = (0, '')
	feat = 'sens'

	if m == 'SVC' or m == 'all':
		svc_grid(fd, feat)
	if m == 'DT' or m == 'all':
		dt_grid(fd, feat)
	if m == 'KN' or m == 'all':
		kn_grid(fd, feat)
	if m == 'RF' or m == 'all':
		rf_grid(fd, feat)
	fd.write('\n' + str(max_svc) + '\n')
	fd.write(str(max_dt) + '\n')
	fd.write(str(max_kn) + '\n')
	fd.write(str(max_rf) +'\n')
	fd.close()
	return 0

if __name__ == '__main__':
	sys.exit(grid_search(sys.argv[1]))
