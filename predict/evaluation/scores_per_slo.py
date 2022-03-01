import subprocess, ast, sys
sys.path.append('../')
from predictor import *
from scipy.stats.mstats import gmean

def f1_calc(file_):
	cmd = 'tail -n1 ' + file_
	last_line = '{' + subprocess.check_output(cmd, shell = True).split('\t')[1].split('{')[1]
	last_line = ast.literal_eval(last_line)

	fs = list()
	ff = file_.split('/')[-1]
	clas = int(ff.split('_')[1])
	for c in range(clas):
		tp = sum(map(lambda x: x[1], filter(lambda y: y[0][0] == c and y[0][1] == c, last_line.items())))
		fn = sum(map(lambda x: x[1], filter(lambda y: y[0][0] != c and y[0][1] == c, last_line.items())))
		fp = sum(map(lambda x: x[1], filter(lambda y: y[0][0] == c and y[0][1] != c, last_line.items())))
		if tp + fp == 0:
			precision = 0
		else:
			precision = float(tp) / (tp + fp)
		if tp + fn == 0:
			recall = 0
		else:
			recall = float(tp) / (tp + fn)
		if precision + recall == 0:
			f = 0.0
		else:
			f = 2.0 * (precision * recall) / (precision + recall)
		fs.append(f)
	return np.mean(fs)

def test_acc_2(iterations = 10):
	features = ['sens', 'cont']
	k = 8
	tool = 'perf'
	lim = 1.3
	clos = [round(0.1 * x, 1) for x in range(11, int(lim * 10 + 1))]
	for mod in ['SVC', 'DT', 'KN', 'RF']:
		for classes in [2, 3]:
			ans = dict()
			fs = dict()
			for feature in features:
				ans[feature] = dict()
				fs[feature] = dict()
				for x in clos:
					ans[feature][x] = []
					fs[feature][x] = []
					max_acc = 0.0
					name = feature + '_' + str(classes) + '_' + str(x) + '_' + mod + '.csv'
					for i in range(iterations):
						acc = predict([x], feature, mod, classes)
						ans[feature][x].append(acc)
						fs[feature][x].append(f1_calc(csv_dir + name))
						if acc > max_acc:
							max_acc = acc
					#		os.rename(csv_dir + name, csv_dir + 'predictions/' + mod + '/' + name)
					try:
						os.remove(csv_dir + name)
					except:
						pass
					print feature, x, "Average:", gmean(filter(lambda x: x>0, ans[feature][x])), gmean(fs[feature][x])
			fd = open(csv_dir + 'adaptivity/' + mod + '_' + str(classes) + '.csv', mode='a+')
			ff = open(csv_dir + 'adaptivity/f1/' + mod + '_' + str(classes) + '.csv', mode = 'a+')
			writer = csv.writer(fd, delimiter=',')
			friter = csv.writer(ff, delimiter=',')
			for x in clos:
				row = [x]
				fow = [x]
				for f in features:
					row.extend([gmean(ans[f][x]), -1])
					fow.extend([gmean(fs[f][x]), -1])
				writer.writerow(row)
				friter.writerow(fow)
			fd.close()
			ff.close()

def f1_2sla(file_):
	cmd = 'tail -n1 ' + file_
	last_line = '{' + subprocess.check_output(cmd, shell = True).split('\t')[1].split('{')[1]
	last_line = ast.literal_eval(last_line)

	fs = list()
	for c in range(3):
		tp = sum(map(lambda x: x[1], filter(lambda y: y[0][0] == c and y[0][1] == c, last_line.items())))
		fn = sum(map(lambda x: x[1], filter(lambda y: y[0][0] != c and y[0][1] == c, last_line.items())))
		fp = sum(map(lambda x: x[1], filter(lambda y: y[0][0] == c and y[0][1] != c, last_line.items())))
		if tp + fp == 0:
			precision = 0
		else:
			precision = float(tp) / (tp + fp)
		if tp + fn == 0:
			recall = 0
		else:
			recall = float(tp) / (tp + fn)
		if precision + recall == 0:
			f = 0.0
		else:
			f = 2.0 * (precision * recall) / (precision + recall)
		fs.append(f)
	return np.mean(fs)

def test_acc_3(iterations = 5):
	features = ['sens', 'cont']
	models = ['SVC', 'DT', 'KN', 'RF']
	k = 8
	tool = 'pqos'
	lim = 1.4
	clos1 = [round(0.1 * x, 1) for x in range(11, int(lim * 10 + 1))]
	clos2 = [round(x + 0.1, 1) for x in clos1]
	ans = dict()
	fs = dict()
	for feature in features:
		ans[feature] = dict()
		fs[feature] = dict()
		for mod in models:
			ans[feature][mod] = dict()
			fs[feature][mod] = dict()
			for c1 in clos1:
				ans[feature][mod][c1] = dict()
				fs[feature][mod][c1] = dict()
				for c2 in clos2:
					if c2 - c1 < 1e-3:
						continue
					qos = [c1,c2]
					max_acc = 0.0
					ans[feature][mod][c1][c2] = []
					fs[feature][mod][c1][c2] = []
					name = feature + '_2_' + str(c1) + ',' + str(c2) + '_' + mod + '.csv'
					for i in range(iterations):
						acc = predict(qos, feature, mod)
						ans[feature][mod][c1][c2].append(acc)
						fs[feature][mod][c1][c2].append(f1_2sla(csv_dir + name))
						if acc > max_acc:
							max_acc = acc
					#		os.rename(csv_dir + name, csv_dir + 'predictions_dslo/' + mod + '/' + name)
					try:
						os.remove(csv_dir + name)
					except:
						pass
	
	fd = open(csv_dir + 'adaptivity/' + 'double_SLA_f1.csv', mode='a+')
	ff = open(csv_dir + 'adaptivity/f1/' + 'double_SLA_f1.csv', mode='a+')
	writer = csv.writer(fd, delimiter=',')
	friter = csv.writer(ff, delimiter=',')
	for mod in models:
		writer.writerow([mod])
		friter.writerow([mod])
		for c1 in clos1:
			row = [c1]
			fow = [c1]
			for f in features:
				for c2 in clos2:
					if c2 - c1 < 1e-3:
						row.append(-1)
						fow.append(-1)
					else:
						row.append(np.mean(ans[f][mod][c1][c2]))
						fow.append(np.mean(fs[f][mod][c1][c2]))
				row.append(-2)
				fow.append(-2)
			writer.writerow(row)
			friter.writerow(fow)
	fd.close()
	ff.close()

if __name__ == '__main__':
	sys.exit(test_acc_3())
	classes = sys.argv[1]
	if classes == '2':
		test_acc_2()
	elif classes == '3':
		test_acc_3()
