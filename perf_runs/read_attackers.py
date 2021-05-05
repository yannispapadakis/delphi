import sys
sys.path.append('../core/')
from read_file import *
sys.path.append('../grid_runs/')
from grid import *
from scipy.stats.mstats import gmean

def sensitivity(qos = 1.2, function = 'geomean'):
	result_dir = home_dir + "results/perf_runs/attackers/"
	total_measures = parse_files(result_dir)
	l3 = dict()
	memBw = dict()

	for f in total_measures:
		bench = f.split('-')[0].replace('_', '-')
		tool = f.split('-')[1].split('.')[0]
		if tool == 'l3':
			l3[bench] =  total_measures[f]['vm_mean_perf'][0]
		elif tool == 'memBw':
			memBw[bench] = total_measures[f]['vm_mean_perf'][0]
	ans = dict()
	for bench in l3:
		bench_sens = (l3[bench], memBw[bench])
		if function == 'geomean':
			bench_sens = int(gmean(bench_sens) > qos)
		elif function == 'boolsum':
			bench_sens = len(filter(lambda x: x > qos, bench_sens))
		ans[bench] = bench_sens
	return ans

def contentiousness(b1, b2, grid, qos = 1.2, function = 'geomean'):
	cont = dict()
	for bench in grid:
		bench_cont = (grid[b1][bench], grid[b2][bench])
		if function == 'geomean':
			bench_cont = int(gmean(bench_cont) > qos)
		elif function == 'boolsum':
			bench_cont = len(filter(lambda x: x > qos, bench_cont))
		cont[bench] = bench_cont
	return cont

def search_combinations(grid, qos = 1.2):
	benchmarks = [x for x in grid if x.endswith('1') or x.endswith('2')]
	sens = dict((bench, gmean(grid[bench].values())) for bench in benchmarks)
	sens = map(lambda x: x[0], sorted(sens.items(), key = lambda x: x[1]))

	gridT = transpose_grid(grid)
	(cos, _, _) = classes(grid, [qos])

	best = ('', 0, [])
	for b1 in sens[:len(sens) - 1]:
		for b2 in sens[sens.index(b1) + 1:]:
			cont = contentiousness(b1, b2, grid)
			accuracy = validate(cont, cos)
			if accuracy > best[1]:
				best = (b1 + '_' + b2, accuracy, cont)
	return best[2]

def validate(answer, clos, qos = 1.2):
	total = len(answer)
	correct = 0
	for bench in answer:
		correct += int(answer[bench] == clos[bench])
	return float(correct) / total

def attacker_classifier():
	grid = generate_grid()
	read_grid(grid)

	sens = sensitivity()
	cont = contentiousness('calculix-2', 'gobmk-1', grid)
	#cont = search_combinations(grid)
	clos = dict()
	for bench in sens:
		clos[bench] = (sens[bench], cont[bench])
	return clos

if __name__ == '__main__':
	cl = attacker_classifier()
