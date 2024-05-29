#!/usr/bin/python3
from predictor import *
from itertools import combinations

accuracies = {}
f1scores = {}
mmm = "ET"
a = specs + parsecs + tails
random.shuffle(a)
step = 10
slice_len = 5
for i in range(10, len(specs + parsecs + tails)):
	to_comb = a[min(max(0, i - slice_len), len(a) - step):min(step + max(i - slice_len, 0), len(a))]
	std_list = a[:min(max(0, i - slice_len), len(a) - step)]
	print(f"Number of benchmarks = {i}")	
	random.shuffle(to_comb)
	if i == len(specs + parsecs + tails) - 1:
		to_comb = a
		std_list = []
	accuracies[i] = {}
	f1scores[i] = {}
	for feat in features:
		print(f"\tFeature: {feat}")
		if feat not in accuracies[i].keys(): accuracies[i][feat] = {}
		if feat not in f1scores[i].keys(): f1scores[i][feat] = {}
		#for slo in qos_levels:
		for slo in [1.1, 1.2]:
			print(f"\t\tSLO: {slo}")
			if slo not in accuracies[i][feat]: accuracies[i][feat][slo] = {}
			if slo not in f1scores[i][feat]: f1scores[i][feat][slo] = {}
			for class_ in classes_:
				print(f"\t\t\tClasses: {class_}: {datetime.datetime.strftime(datetime.datetime.now(), '%H:%M:%S')}")
				accuracies[i][feat][slo][class_] = []
				f1scores[i][feat][slo][class_] = []
				for c in combinations(to_comb, i - len(std_list)):
					train_set = std_list + list(c)
					test_set = list(set(specs + parsecs + tails).difference(train_set))
					res = prediction(['test', feat, slo, class_, mmm, train_set, test_set])
					if res:
						accuracies[i][feat][slo][class_].append(res[0])
						f1scores[i][feat][slo][class_].append(res[1])
				accuracies[i][feat][slo][class_] = np.mean(accuracies[i][feat][slo][class_])
				f1scores[i][feat][slo][class_] = np.mean(f1scores[i][feat][slo][class_])
print('='*200)
pprint.pprint(accuracies)
print('='*200)
pprint.pprint(f1scores)
