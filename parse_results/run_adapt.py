from predictor import *

def test_acc_2(iterations = 20):
	features = ['sens', 'cont']
	k = 8
	tool = 'pqos'
	lim = 1.8
	source = '/home/ypap/actimanager/workload/parse_results/csv/'
	clos = [round(0.1 * x, 1) for x in range(11, int(lim * 10 + 1))]
	for q in ['', 'q']:
		ans = dict()
		for feature in features:
			ans[feature] = dict()
			for x in clos:
				ans[feature][x] = []
				max_acc = 0.0
				for i in range(iterations):
					acc = predict(k, [x], tool, feature, q)
					ans[feature][x].append(acc)
					if acc > max_acc:
						max_acc = acc
						qq = '_q' if q == 'q' else ''
						name = feature + qq + '_' + str(x) + '.csv'
						os.rename(source + name, source + '/predictions/' + name)
		fd = open('csv/adaptivity/adapt2' + q + '.csv', mode='a+')
		writer = csv.writer(fd, delimiter=',')
		for x in clos:
			row = [x]
			for f in features:
				row.extend([np.mean(ans[f][x]), -1])
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

def test_acc_4(iterations = 20):
	features = ['sens', 'cont']
	k = 8
	tool = 'pqos'
	lim = 2.0
	clos1 = [round(0.1 * x, 1) for x in range(11, int(lim * 10 + 1))]
	clos2 = [round(x + 0.1, 1) for x in clos1]
	clos3 = [round(x + 0.1, 1) for x in clos2]
	ans = dict()
	for feature in features:
		ans[feature] = dict()
		for c1 in clos1:
			ans[feature][c1] = dict()
			for c2 in clos2:
				if c2 - c1 < 1e-3:
					continue
				ans[feature][c1][c2] = dict()
				for c3 in clos3:
					if c3 - c2 < 1e-3:
						continue
					qos = [c1,c2,c3]
					ans[feature][c1][c2][c3] = []
					for i in range(iterations):
						ans[feature][c1][c2][c3].append(predict(k, qos, tool, feature))
	
	fd = open('csv/adaptivity/adapt4.csv', mode='a+')
	writer = csv.writer(fd, delimiter=',')
	for c1 in clos1:
		headd = [c1]
		for f in features:
			headd += clos3
			headd += [-2]
		writer.writerow(headd)
		for c2 in clos2:
			if c2 - c1 < 1e-3:
				continue
			for i in range(iterations):
				row = [c2]
				for f in features:	
					for c3 in clos3:
						if c3 - c2 < 1e-3:
							row.append(-1)
						else:
							row.append(ans[f][c1][c2][c3][i])
					row.append(-2)
				writer.writerow(row)
	fd.close()

if __name__ == '__main__':
	classes = sys.argv[1]
	if classes == '2':
		test_acc_2()
	elif classes == '3':
		test_acc_3()
