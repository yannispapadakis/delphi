#!/usr/bin/python3
import sys
sys.path.append('../core/')
from read_vm_output import *

########################################## PQOS Parser ############################################

def read_pqos_files(pqos_file, run_periods):
	pqos_f = open(isolation_dir + 'pqos/' + pqos_file, 'r')
	rd = csv.reader(pqos_f)
	pqos_measures = dict()
	for row in rd:
		if row[0] == 'Time':
			events = list(map(lambda x: x.lower(), row[2:]))
			for event in events:
				pqos_measures[event] = []
		else:
			time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours=3 if 'tailbench' in pqos_file else 2)
			time = int(time.strftime("%s"))
			if time < run_periods[0] or time > run_periods[1]:
				continue
			measure = row[2:]
			for (i, event) in list(enumerate(events)):
				pqos_measures[event].append(float(measure[i]))
	return pqos_measures

########################################## Perf Parser ############################################

def read_perf_file(filename, directory, run_periods):
	measures = OrderedDict()
	with open(directory + filename) as perf_f:
		name = filename.split('.')[1]
		line = perf_f.readline()
		while line:
			tokens = line.split()
			if len(tokens) == 0:
				line = perf_f.readline()
				continue
			if tokens[0] == '#' or '<not' in tokens or 'counted>' in tokens:
				if tokens[1] == 'started':
					start_t = datetime.datetime.strptime(' '.join(tokens[4:]), "%b %d %H:%M:%S %Y")
					if filename.startswith('parsec'):
						start_t = start_t - datetime.timedelta(hours=2)
					if filename.startswith('tailbench'):
						start_t = start_t - datetime.timedelta(hours=3)
					start_t = int(start_t.strftime("%s"))
				line = perf_f.readline()
				continue
			time = int(tokens[0].split('.')[0]) + start_t
			if time < run_periods[0] or time > run_periods[1]:
				line = perf_f.readline()
				continue
			event = tokens[2]
			value = int(tokens[1])
			if event in measures:
				measures[event].append(value)
			else:
				measures[event] = [value]
			line = perf_f.readline()
		perf_f.close()
	if 'instructions' in measures and 'cycles' in measures:
		measures['ipc_perf'] = map(lambda x: float(x[0]) / x[1] if x[1] > 0 else 0, 
							  list(zip(measures['instructions'], measures['cycles'])))
		measures.pop('cycles')
	return measures

def apply_mean(all_measures):
	for bench in all_measures:
		if bench == 'Title': continue
		measures = all_measures[bench]
		for event in measures:
			measures[event] = np.mean(list(measures[event]))
			#measures[event] = gmean(list(filter(lambda x: x > 0, measures[event])))

def perf_to_csv(measures, name):
	out_file = open(isolation_dir + 'perf/csv_files/' + csv_dir + name + '_perf.csv', 'w')
	writer = csv.writer(out_file)
	events = measures.keys()
	writer.writerow(events)
	for i in range(max(map(len, list(measures.values())))):
		row = []
		for key in events:
			try:
				row.append(str(measures[key][i]))
			except:
				row.append('')
		writer.writerow(row)
	out_file.close()

def mpki_calculation(all_measures):
	for bench in all_measures:
		measures = all_measures[bench]
		measures['branch-misses'] = list(map(lambda x: (float(x[0]) / x[1]) if x[1] > 0 else 0,
									list(zip(measures['branch-misses'], measures['branch-instructions']))))
		measures['dTLB-misses'] = list(map(sum, list(zip(measures['dTLB-load-misses'], measures['dTLB-store-misses']))))
		measures.pop('dTLB-load-misses')
		measures.pop('dTLB-store-misses')
		for event in [x for x in measures if 'miss' in x and 'branch' not in x]:
			measures[event] = list(map(lambda x: (x[0] * 1000.0 / x[1]) if x[1] > 0 else 0,
									list(zip(measures[event], measures['instructions']))))
		measures.pop('branch-instructions')
		measures.pop('instructions')

def attach_pqos(all_measures):
	run_periods = time_cleanup('pqos')
	pqos_files = os.listdir(isolation_dir + 'pqos/raw_measures/')
	for pqos_file in list(filter(lambda x: x.endswith('csv'), pqos_files)):
		if pqos_file.split('.')[1] in excluded_benchmarks: continue
		bs = ae = alll = 0
		pqos_f = open(isolation_dir + 'pqos/raw_measures/' + pqos_file, 'r')
		rd = csv.reader(pqos_f)
		pqos_measures = dict()
		for row in rd:
			if row[0] == 'Time':
				events = list(map(lambda x: x.lower(), row[2:]))
				for event in events:
					pqos_measures[event] = []
			else:
				time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours=3 if 'tailbench' in pqos_file else 2)
				time = int(time.strftime("%s"))
				if time < run_periods[pqos_file.split('.')[1]][0] or time > run_periods[pqos_file.split('.')[1]][1]:
					continue
				measure = row[2:]
				for (i, event) in list(enumerate(events)):
					pqos_measures[event].append(float(measure[i]))
		for event in pqos_measures:
			name = pqos_file.split('.csv')[0] if "sphinx-" in pqos_file else pqos_file.split('.')[1]
			all_measures[name][event] = pqos_measures[event]

############################################# Main ################################################

def write_perf_measures(all_measures):
	out_file = open(isolation_dir + 'perf/accumulated/perf_measures.csv', 'w')
	writer = csv.writer(out_file)
	for bench in all_measures:
		writer.writerow(all_measures[bench])
	out_file.close()

def read_perf_measures():
	try: in_file = open(isolation_dir + 'perf/accumulated/perf_measures.csv', 'r')
	except: return {}
	reader = csv.reader(in_file)
	measures = dict()
	for row in reader:
		if row[0] == "Benchmark": measures['Title'] = row
		else: measures[row[0]] = [row[0]] + list(map(float, row[1:]))
	return measures

def perf_files(tool = 'pqos'):
	version = ''
	if len(tool.split('-')) == 2:
		(tool, version) = tool.split('-')
	directory = isolation_dir + tool + ('-' + version if version != '' else '') + '/raw_measures/'
	files = list(filter(lambda x: x.endswith('csv'), os.listdir(directory)))
	all_measures = dict()
	if tool == 'pqos':
		all_measures['Title'] = ['Benchmark', 'IPC', 'LLC_Misses', 'LLC', 'MBL', 'MBR', 'Vcpus', 'Class']
		run_periods = time_cleanup('pqos')
		for f in list(filter(lambda x: x.endswith('csv'), files)):
			bench = f.split('.')[1]
			if bench in excluded_benchmarks: continue
			measures = read_pqos_files(f, run_periods[bench])
			for event in measures:
				measures[event] = np.mean(measures[event])
			all_measures[bench] = [bench] + list(measures.values()) + [int(bench.replace('img-dnn', 'imgdnn').split('-')[1])]
	elif tool == 'perf':
		cached_measures = read_perf_measures()
		if len(files) == len(list(cached_measures.keys())): return cached_measures
		else:
			final_title = []
			run_periods = time_cleanup('perf')
			for f in list(filter(lambda x: x.endswith('csv'), files)):
				if f.split('.')[1] in excluded_benchmarks: continue
				measures = read_perf_file(f, directory, run_periods[f.split('.')[1]])
				if final_title == []: final_title = measures.keys()
				elif final_title != measures.keys(): print("Title error on:", f)
				name = f.split('.csv')[0] if 'sphinx-' in f else f.split('.')[1]
				all_measures[name] = measures
			if version == '':
				attach_pqos(all_measures)
				mpki_calculation(all_measures)
				apply_mean(all_measures)
				for bench in all_measures:
					final_title = list(all_measures[bench].keys())
					all_measures[bench] = [bench] + list(all_measures[bench].values())
				all_measures['Title'] = ['Benchmark'] + final_title + ['Class']
				write_perf_measures(all_measures)
			elif version == 'sp':
				apply_mean(all_measures)
				for bench in all_measures:
					all_measures[bench].pop('instructions')
					final_title = list(all_measures[bench].keys())
					all_measures[bench] = [bench] + list(all_measures[bench].values())
				all_measures['Title'] = ['Benchmark'] + final_title + final_title + ['Slowdown']
	return all_measures

def time_cleanup(tool = 'perf'):
	directory = isolation_dir + tool + '/outputs/'
	total_measures = parse_files(directory)
	run_periods = dict()
	for f in total_measures:
		bench_name = f.replace('img-dnn', 'imgdnn').split('-')[0].replace('_','-').replace('imgdnn', 'img-dnn')
		run_periods[bench_name] = (min(total_measures[f]['vm_event_times'][0]), max(total_measures[f]['vm_event_times'][0]))
	return run_periods

if __name__ == '__main__':
	perf_files(sys.argv[1])
