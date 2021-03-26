from grid import *
qos = [1.2]

def box_plots_per_benchmark(grid, clos, mode):
	out_file = csv_dir + "bp_benchmark_" + mode + ".csv"
	fd = open(out_file, mode = 'w')
	writer = csv.writer(fd, delimiter='\t')
	for bench in grid.keys():
		measures = map(float, grid[bench].values())
		quantile3 = np.percentile(measures,75)
		median = np.percentile(measures,50)
		quantile1 = np.percentile(measures,25)
		iqr = quantile3 - quantile1
		lower_whisker_lim = quantile1 - 1.5 * iqr
		upper_whisker_lim = quantile3 + 1.5 * iqr
		lower_whisker = min([x for x in measures if x >= lower_whisker_lim])
		upper_whisker = max([x for x in measures if x <= upper_whisker_lim])
		writer.writerow([bench, lower_whisker, quantile1, median, quantile3, upper_whisker])

def box_plots_per_class(grid, clos, mode):
	out_file = csv_dir + "bp_class_" + mode + ".csv"
	fd = open(out_file, mode = 'w')
	writer = csv.writer(fd, delimiter='\t')
	classes = set(clos.values())
	per_class = dict((c,[]) for c in classes)
	for bench in grid.keys():
		measures = map(float, grid[bench].values())
		per_class[clos[bench]].extend(measures)
	for c in per_class:
		total = per_class[c]
		quartile3 = np.percentile(total, 75)
		median = np.percentile(total, 50)
		quartile1 = np.percentile(total, 25)
		iqr = quartile3 - quartile1
		lower_lim = quartile1 - 1.5 * iqr
		upper_lim = quartile3 + 1.5 * iqr
		l_whisker = min([x for x in total if x >= lower_lim])
		u_whisker = max([x for x in total if x <= upper_lim])
		writer.writerow([c, l_whisker, quartile1, median, quartile3, u_whisker])

def box_plots_per_cvc(grid, clos, closC):
	out_file = csv_dir + 'box_plots_cvc.csv'
	fd = open(out_file, mode = 'w')
	writer = csv.writer(fd, delimiter='\t')
	classes = set(clos.values())
	per_cvc = dict( (c, dict((cc, []) for cc in classes)) for c in classes)
	for bench in grid.keys():
		for c in classes:
			benches_measures = [grid[bench][x] for x in grid[bench] if closC[x] == c]
			per_cvc[clos[bench]][c].extend(benches_measures)
	for c in classes:
		for cc in classes:
			total = per_cvc[c][cc]
			quartile3 = np.percentile(total, 75)
			median = np.percentile(total, 50)
			quartile1 = np.percentile(total, 25)
			iqr = quartile3 - quartile1
			lower_lim = quartile1 - 1.5 * iqr
			upper_lim = quartile3 + 1.5 * iqr
			l_whisker = min([x for x in total if x >= lower_lim])
			u_whisker = max([x for x in total if x <= upper_lim])
			writer.writerow([c,cc, l_whisker, quartile1, median, quartile3, u_whisker])

def plot_make_grid(feature = 'sens', q = '', qos = [1.2]):
	grid = generate_grid()
	ok = read_grid(grid)
	if not ok:
		calculate_grid(grid)
	if feature == 'cont':
		grid = transpose_grid(grid)
	(clos, _, _) = classes(grid, qos, q)
	return (grid, clos)

if __name__ == "__main__":
	try:
		q = sys.argv[2]
		q = 'q'
	except:
		q = ''
	(sens_grid, sens_clos) = plot_make_grid('sens', q)
	cont_grid = transpose_grid(sens_grid)
	(cont_clos, _, _) = classes(cont_grid, qos, q)

	if sys.argv[1] == "":
		mode = raw_input("Choose a mode: (bench, class, cvc, c-all, all): ")
	else:
		mode = sys.argv[1]
	if mode == "bench" or mode == "all":
		box_plots_per_benchmark(sens_grid, sens_clos, 'sens')
		box_plots_per_benchmark(cont_grid, cont_clos, 'cont')
	elif mode == "class" or mode == "all" or mode == "c-all":
		box_plots_per_class(sens_grid, sens_clos, 'sens')
		box_plots_per_class(cont_grid, cont_clos, 'cont')
	elif mode == "cvc" or mode == "all" or mode == "c-all":
		box_plots_per_cvc(sens_grid, sens_clos, cont_clos)
