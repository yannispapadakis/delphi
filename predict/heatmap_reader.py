#!/usr/bin/python3
import sys
sys.path.append('../core/')
from read_vm_output import *
from isolation_reader import *

csv_dir = home_dir + 'results/'
grid_dir = csv_dir + 'heatmaps/'

vcpus = ['1', '2', '4', '8']

def generate_grid(benchmarks = []):
	grid = OrderedDict()
	if benchmarks == []: benchmarks = os.listdir(pairs_dir)
	for b in benchmarks:
		if '-' in b:
			grid[b] = OrderedDict()
		else:
			for v in vcpus:
				bench = b + '-' + v
				grid[bench] = OrderedDict()
	return grid

def read_grid(grid, name = 'grid', include = []):
	gridfile = grid_dir + name + '.csv'
	try:
		fd = open(gridfile)
	except:
		return False
	gridread = csv.reader(fd, delimiter='\t')
	new_files = []
	for row in gridread:
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
					grid[bench1][bench2] = float(sd)
				else:
					(b1, v1) = bench1.split('-')
					(b2, v2) = bench2.split('-')
					if int(v1) + int(v2) > 10 or int(v1) > int(v2):
						continue
					search_dir = pairs_dir + b1 + '/' + v1 + 'vs' + v2 + '/'
					try:
						files = os.listdir(search_dir)
					except:
						continue
					fname = b1 + '_' + v1 + '-' + b2 + '_' + v2 + '.txt'
					if fname in files or fname.replace('-','.') in files:
						new_files.append(fname)
	fd.close()

	dirs = []
	for run in new_files:
		benches = run.split('.')[0].split('-')
		(b1, v1) = benches[0].split('_')
		(b2, v2) = benches[1].split('_')
		dirs.append(pairs_dir + b1 + '/' + v1 + 'vs' + v2 + '/')
	if dirs != []:
		fill_missing(grid, dirs)
	return True

def fill_missing(grid, dirs):
	for directory in dirs:
		total_measures = parse_files(directory)
		for f in total_measures:
			measures = total_measures[f]
			(name_0, name_1) = (measures['vms_names'][0], measures['vms_names'][1])
			name_0 = name_0.split('-')[3] if 'parsec' in name_0 else name_0.split('-')[3].split('.')[1]
			name_1 = name_1.split('-')[3] if 'parsec' in name_1 else name_1.split('-')[3].split('.')[1]
			(vcpus_0, vcpus_1) = (str(measures['vms_vcpus'][0]), str(measures['vms_vcpus'][1]))
			bench1 = name_0 + '-' + vcpus_0
			bench2 = name_1 + '-' + vcpus_1
			grid[bench1][bench2] = measures['vm_mean_perf'][0]
			grid[bench2][bench1] = measures['vm_mean_perf'][1]

def calculate_grid(grid):
	dirs = []
	benchmarks = [x.split('-')[0] for x in grid.keys()]
	for bench in benchmarks:
		bench_dir = pairs_dir + bench + '/'
		combinations = os.listdir(bench_dir)
		for combination in combinations:
			dd = bench_dir + combination + '/'
			if len(os.listdir(dd)) == 0: continue
			if dd not in dirs:
				dirs.append(dd)
	fill_missing(grid, dirs)

def transpose_grid(grid, include = []):
	keys = grid.keys()
	gridT = generate_grid(include)
	for col in keys:
		for row in keys:
			try:
				gridT[col][row] = grid[row][col]
			except KeyError:
				continue
	return gridT

def qos_class(qos, slowdown):
	try:
		class_ = qos.index(min([x for x in qos if x > slowdown]))
	except:
		class_ = len(qos)
	return class_

def qos_class_new(qos, whisker, q3):
	try:
		w_class = qos.index(min([x for x in qos if x > whisker]))
	except:
		w_class = len(qos)
	try:
		q_class = qos.index(min([x for x in qos if x > q3]))
	except:
		q_class = len(qos)
	return w_class + q_class

def classes(grid, qos, class_num = 2):
	clos = dict()
	whiskers = dict()
	quartiles3 = dict()
	for bench in grid.keys():
		if not grid[bench]: continue
		measures = list(map(float, grid[bench].values()))
		quartile3 = np.percentile(measures,75)
		quartile1 = np.percentile(measures,25)
		iqr = quartile3 - quartile1
		whisker_lim = quartile3 + 1.5 * iqr
		whisker = max([x for x in measures if x <= whisker_lim])
		if class_num == 2:
			clos[bench] = qos_class(qos, whisker)
		elif class_num == 3:
			clos[bench] = qos_class_new(qos, whisker, quartile3)
		whiskers[bench] = whisker
		quartiles3[bench] = quartile3
	return (clos, whiskers, quartiles3)

def print_grid(grid, T = False, name = 'grid'):
	out_file = grid_dir + name + "T.csv" if T else grid_dir + name + ".csv"
	fd = open(out_file, mode='w')
	writer = csv.writer(fd, delimiter='\t')

	writer.writerow([''] + list(grid.keys()))
	
	for bench1 in grid.keys():
		print_line = [bench1]
		for bench2 in grid.keys():
			try:
				print_line.append(grid[bench1][bench2])
			except:
				print_line.append('0')
		writer.writerow(print_line)
	fd.close()

def clean_grid(grid):
	removed = []
	for bench in grid:
		if not grid[bench]:
			removed.append(bench)
	for bench in removed:
		del grid[bench]

def make_grid(feature = 'sens', qos = [1.2], class_num = 2):
	grid = generate_grid()
	ok = read_grid(grid)
	if not ok:
		calculate_grid(grid)
	if feature == 'cont':
		grid = transpose_grid(grid)
	if not ok:
		clean_grid(grid)
		print_grid(grid, feature == 'cont')
	return classes(grid, qos, class_num)

def make_partial_grid(benchmarks, feature = 'sens', qos = [1.2], class_num = 2):
	grid = generate_grid(benchmarks)
	ok = read_grid(grid, include = benchmarks)
	if feature == 'cont':
		grid = transpose_grid(grid, benchmarks)
	return classes(grid, qos, class_num)

if __name__ == '__main__':
	make_grid()
