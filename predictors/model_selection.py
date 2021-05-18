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
