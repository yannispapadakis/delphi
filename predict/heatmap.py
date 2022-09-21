#!/usr/bin/python3
from isolation_reader import *

def spawn_heatmap(benchmarks = []):
	if benchmarks == []:
		benchmarks = [x + '-' + y for x in os.listdir(coexecutions_dir) for y in vcpus]
	benchmarks = list(filter(lambda x: x not in excluded_benchmarks, benchmarks))
	return OrderedDict((b, OrderedDict()) for b in benchmarks)

def read_heatmap(heatmap, name = 'heatmap'):
	hm_file = heatmap_dir + name + '.csv'
	try:
		fd = open(hm_file)
	except:
		write_heatmap()
		fd = open(hm_file)
	hm_read = csv.reader(fd, delimiter='\t')
	new_files = []
	for row in hm_read:
		if row[0] == '':
			benchmarks = row
		else:
			bench1 = row[0]
			if bench1 not in heatmap.keys(): continue
			for (i, sd) in enumerate(row):
				if i == 0: continue
				bench2 = benchmarks[i]
				if bench2 not in heatmap.keys(): continue
				if float(sd) > 0:
					heatmap[bench1][bench2] = float(sd)
	fd.close()
	clean_heatmap(heatmap)

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
			if bench1 not in heatmap.keys() or bench2 not in heatmap.keys(): continue
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
	clean_heatmap(heatmap)

def transpose_heatmap(heatmap):
	keys = heatmap.keys()
	heatmapT = spawn_heatmap(keys)
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

def print_heatmap(heatmap, T = '', name = 'heatmap'):
	out_file = heatmap_dir + name + T + ".csv"
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
	for b in list(filter(lambda x: heatmap[x] == {}, list(heatmap.keys()))): del heatmap[b]

def get_heatmap(benchmarks, feature = 'sens', qos = 1.2, class_num = 3):
	heatmap = spawn_heatmap(benchmarks)
	read_heatmap(heatmap)
	if feature == 'cont':
		heatmap = transpose_heatmap(heatmap)
	return classes(heatmap, qos, class_num)

def write_heatmap():
	heatmap = spawn_heatmap([])
	calculate_heatmap(heatmap)
	print_heatmap(heatmap)
	print_heatmap(transpose_heatmap(heatmap), 'T')

if __name__ == '__main__':
	write_heatmap()
