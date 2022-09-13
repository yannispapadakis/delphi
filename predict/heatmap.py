#!/usr/bin/python3
from isolation_reader import *

def spawn_heatmap(benchmarks = []):
	if benchmarks == []:
		benchmarks = [x + '-' + y for x in os.listdir(coexecutions_dir) for y in vcpus]
	benchmarks = list(filter(lambda x: x not in excluded_benchmarks, benchmarks))
	return OrderedDict((b, OrderedDict()) for b in benchmarks)

def read_heatmap(heatmap, name = 'heatmap', include = []):
	hm_file = heatmap_dir + name + '.csv'
	try:
		fd = open(hm_file)
	except:
		return False
	hm_read = csv.reader(fd, delimiter='\t')
	new_files = []
	for row in hm_read:
		if row[0] == '':
			benchmarks = row
			if include == []: include = benchmarks
		else:
			bench1 = row[0]
			if bench1 not in include: continue
			for (i, sd) in enumerate(row):
				if i == 0: continue
				bench2 = benchmarks[i]
				if bench2 not in include: continue
				if float(sd) > 0:
					heatmap[bench1][bench2] = float(sd)
				else:
					(b1, v1) = bench1.replace('img-dnn', 'imgdnn').split('-')
					(b2, v2) = bench2.replace('img-dnn', 'imgdnn').split('-')
					(b1, b2) = (b1.replace('imgdnn', 'img-dnn'), b2.replace('imgdnn', 'img-dnn'))
					if int(v1) + int(v2) > 10: continue
					search_dir = coexecutions_dir + b1 + '/' + v1 + 'vs' + v2 + '/'
					try: files = os.listdir(search_dir)
					except: continue
					fname = b1 + '_' + v1 + '-' + b2 + '_' + v2 + '.txt'
					if fname in files or fname.replace('-','.') in files:
						new_files.append(fname)
	fd.close()

	dirs = []
	for run in new_files:
		benches = run.split('.')[0].split('-')
		(b1, v1) = benches[0].split('_')
		(b2, v2) = benches[1].split('_')
		dirs.append(coexecutions_dir + b1 + '/' + v1 + 'vs' + v2 + '/')
	if dirs != []:
		fill_missing(heatmap, dirs)
	return True

def fill_missing(heatmap, dirs):
	for directory in dirs:
		total_measures = parse_files(directory)
		for f in total_measures:
			measures = total_measures[f]
			(name_0, name_1) = (measures['vms_names'][0], measures['vms_names'][1])
			name_0 = name_0.replace('img-dnn', 'imgdnn')
			name_0 = name_0.split('-')[3] if 'parsec' in name_0 else name_0.split('-')[2 + int('spec' in name_0)].split('.')[1]
			name_0 = name_0.replace('imgdnn', 'img-dnn')
			name_1 = name_1.split('-')[3] if 'parsec' in name_1 else name_1.split('-')[3].split('.')[1]
			(vcpus_0, vcpus_1) = (str(measures['vms_vcpus'][0]), str(measures['vms_vcpus'][1]))
			bench1 = name_0 + '-' + vcpus_0
			bench2 = name_1 + '-' + vcpus_1
			heatmap[bench1][bench2] = measures['vm_mean_perf'][0]
			heatmap[bench2][bench1] = measures['vm_mean_perf'][1]

def calculate_heatmap(heatmap):
	dirs = []
	benchmarks = [x.replace('img-dnn','imgdnn').split('-')[0].replace('imgdnn', 'img-dnn') for x in heatmap.keys()]
	for bench in benchmarks:
		bench_dir = coexecutions_dir + bench + '/'
		combinations = os.listdir(bench_dir)
		for combination in combinations:
			dd = bench_dir + combination + '/'
			if len(os.listdir(dd)) == 0: continue
			if dd not in dirs: dirs.append(dd)
	fill_missing(heatmap, dirs)

def transpose_heatmap(heatmap, include = []):
	keys = heatmap.keys()
	heatmapT = spawn_heatmap(include)
	for col in keys:
		for row in keys:
			try:
				heatmapT[col][row] = heatmap[row][col]
			except KeyError:
				continue
	return heatmapT

def classes(heatmap, qos, class_num = 2):
	clos = dict()
	whiskers = dict()
	quartiles3 = dict()
	for bench in heatmap.keys():
		if not heatmap[bench]: continue
		measures = list(map(float, heatmap[bench].values()))
		(q3, q1) = (np.percentile(measures, 75), np.percentile(measures, 25))
		iqr = q3 - q1
		whisker = max(filter(lambda x: x <= (q3 + 1.5 * iqr), measures))
		clos[bench] = int(whisker > qos) + int(q3 > qos if class_num == 3 else 0.0)
		whiskers[bench] = whisker
		quartiles3[bench] = q3
	return (clos, whiskers, quartiles3)

def print_heatmap(heatmap, T = False, name = 'heatmap'):
	out_file = heatmap_dir + name + "T.csv" if T else heatmap_dir + name + ".csv"
	fd = open(out_file, mode='w')
	writer = csv.writer(fd, delimiter='\t')

	writer.writerow([''] + list(heatmap.keys()))
	for bench1 in heatmap.keys():
		print_line = [bench1]
		for bench2 in heatmap.keys():
			try: print_line.append(heatmap[bench1][bench2])
			except: print_line.append('0')
		writer.writerow(print_line)
	fd.close()

def clean_heatmap(heatmap):
	removed = []
	for bench in heatmap:
		if not heatmap[bench]: removed.append(bench)
	for bench in removed: del heatmap[bench]

def get_heatmap(benchmarks, feature = 'sens', qos = 1.2, class_num = 3):
	heatmap = spawn_heatmap(benchmarks)
	ok = read_heatmap(heatmap, include = benchmarks)
	if not ok:
		calculate_heatmap(heatmap)
	if feature == 'cont':
		heatmap = transpose_heatmap(heatmap, benchmarks)
	if not ok:
		clean_heatmap(heatmap)
		print_heatmap(heatmap, feature == 'cont')
	return classes(heatmap, qos, class_num)

if __name__ == '__main__':
	get_heatmap([])
