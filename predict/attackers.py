#!/usr/bin/python3
from heatmap import *
from scipy.stats.mstats import gmean

def attacker_classifier(feature, qos, clos):
	includes = ['l3', 'memBw']
	def class_calculate(bench_class, qos, clos):
		if clos == 2: return int(gmean(bench_class) > qos)
		if clos == 3: return min(len(list(filter(lambda x: x > qos, bench_class))), clos - 1)

	def sensitivity(qos, clos):
		total_measures = parse_files(f"{isolation_dir}attackers/")
		predictions = dict()

		for f in total_measures:
			ff = f.replace('img-dnn', 'imgdnn')
			bench = ff.split('-')[0].replace('_', '-').replace('imgdnn', 'img-dnn')
			tool = ff.split('-')[1].split('.')[0]
			if bench not in predictions: predictions[bench] = dict()
			predictions[bench][tool] = total_measures[f]['vm_mean_perf'][0]
		sens = dict()
		for bench in predictions:
			bench_sens = [predictions[bench][tool] for tool in includes]
			sens[bench] = class_calculate(bench_sens, qos, clos)
		return sens
		
	def contentiousness(b1, b2, heatmap, qos, clos):
		cont = dict()
		for bench in heatmap:
			bench_cont = [heatmap[b1][bench], heatmap[b2][bench]]
			cont[bench] = class_calculate(bench_cont, qos, clos)
		return cont

	def search_combinations(heatmap, qos, clos):
		benchmarks = [x for x in heatmap if x.endswith('1') or x.endswith('2')]
		sens = dict((bench, gmean(list(heatmap[bench].values()))) for bench in benchmarks)
		sens = list(map(lambda x: x[0], sorted(sens.items(), key = lambda x: x[1])))

		heatmapT = transpose_heatmap(heatmap)
		(cos, _, _) = classes(heatmap, qos, clos)
		best = ('', 0, [])
		for b1 in sens[:len(sens) - 1]:
			for b2 in sens[sens.index(b1) + 1:]:
				cont = contentiousness(b1, b2, heatmap, qos, clos)
				accuracy = accuracy_calc(cont, cos)
				if accuracy > best[1]: best = (f"{b1}_{b2}", accuracy, cont)
		print(f"{qos} | {clos}: {best[0]}")
		return best[2]

	def accuracy_calc(answer, clos):
		return sum([int(answer[bench] == clos[bench]) for bench in answer]) / float(len(answer))

	if feature == 'sens': return sensitivity(qos, clos)
	elif feature == 'cont':
		if clos == 2: (b1, b2) = ("vips-1" if qos < 1.15 else "x264-2", "masstree-1")
		elif clos == 3:
			(b1, b2) = ("x264-2", "sphinx3-1" if qos < 1.15 else "freqmine-2")
		heatmap = spawn_heatmap()
		read_heatmap(heatmap)
		return contentiousness(b1, b2, heatmap, qos, clos)

if __name__ == '__main__':
	for qos in qos_levels:
		for c in classes_:
			for x in features:
				attacker_classifier(x, qos, c)
