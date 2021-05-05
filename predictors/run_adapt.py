from predictor import *
from scipy.stats.mstats import gmean

def test_acc_2(iterations = 10):
	features = ['sens', 'cont']
	k = 8
	tool = 'perf'
	lim = 1.7
	clos = [round(0.1 * x, 1) for x in range(11, int(lim * 10 + 1))]
	for mod in ['SVC', 'DT', 'KN', 'RF']:
		for classes in [2, 3]:
			ans = dict()
			for feature in features:
				ans[feature] = dict()
				for x in clos:
					ans[feature][x] = []
					max_acc = 0.0
					name = feature + '_' + str(classes) + '_' + str(x) + '_' + mod + '.csv'
					for i in range(iterations):
						acc = predict([x], feature, mod, classes)
						ans[feature][x].append(acc)
						if acc > max_acc:
							max_acc = acc
							os.rename(csv_dir + name, csv_dir + 'predictions/' + mod + '/' + name)
					try:
						os.remove(csv_dir + name)
					except:
						pass
					print feature, x, "Average:", gmean(filter(lambda x: x>0, ans[feature][x]))
			fd = open(csv_dir + 'adaptivity/' + mod + '_' + str(classes) + '.csv', mode='a+')
			writer = csv.writer(fd, delimiter=',')
			for x in clos:
				row = [x]
				for f in features:
					row.extend([gmean(ans[f][x]), -1])
				writer.writerow(row)
			fd.close()

def test_acc_3(iterations = 20):
	features = ['sens', 'cont']
	k = 8
	tool = 'pqos'
	lim = 1.8
	clos1 = [round(0.1 * x, 1) for x in range(11, int(lim * 10 + 1))]
	clos2 = [round(x + 0.1, 1) for x in clos1]
	ans = dict()
	for feature in features:
		ans[feature] = dict()
		for c1 in clos1:
			ans[feature][c1] = dict()
			for c2 in clos2:
				if c2 - c1 < 1e-3:
					continue
				qos = [c1,c2]
				ans[feature][c1][c2] = []
				for i in range(iterations):
					ans[feature][c1][c2].append(predict(k, qos, tool, feature))
	
	fd = open('csv/adaptivity/adapt3.csv', mode='a+')
	writer = csv.writer(fd, delimiter=',')
	for c1 in clos1:
		row = [c1]
		for f in features:	
			for c2 in clos2:
				if c2 - c1 < 1e-3:
					row.append(-1)
				else:
					row.append(np.mean(ans[f][c1][c2]))
			row.append(-2)
		writer.writerow(row)
	fd.close()

if __name__ == '__main__':
	sys.exit(test_acc_2())
	classes = sys.argv[1]
	if classes == '2':
		test_acc_2()
	elif classes == '3':
		test_acc_3()
