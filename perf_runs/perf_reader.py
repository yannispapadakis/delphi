import os, csv, sys
import numpy as np
from scipy.stats.mstats import gmean
from collections import OrderedDict
from operator import add
import pprint

########################################### PCM Parser ###########################################

perf_directory = '/home/ypap/characterization/perf_runs/results/'
csv_dir = '/home/ypap/characterization/parse_results/csv/'

def pcm_measures(filename, directory):
	fd = open(directory + filename)
	measure = csv.reader(fd, delimiter=',')
	platform = []
	measures = OrderedDict()

	for row in measure:
		if row[0] == "System":
			label = row[0]
			for x in row:
				if x != "":
					label = x
				platform.append(label)
		if row[0] == "Date":
			for (p, m) in zip(platform, row):
				measures[(p, m)] = []
		if row[0].startswith('2'):
			for (i, x) in enumerate(row):
				try:
					measures[measures.keys()[i]].append(float(x))
				except:
					measures[measures.keys()[i]].append(x)
	fd.close()
	return measures

def cleanup_keys(measures):
	keys_start = measures.keys()

	for c in keys_start:
		if 'res%' in c[1] or 'INSTnom' in c[1] or "Date" in c[1] or "Time" in c[1] or c[1] == '':
			measures.pop(c, None)

def cores_accumulate(measures):
	keys_start = measures.keys()
	cores = OrderedDict()

	for c in keys_start:
		if 'Core' in c[0]:
			if c[1] not in cores:
				cores[c[1]] = []

	for x in measures:
		if 'Core' in x[0]:
			cores[x[1]] += measures[x]

	return cores

def finalize_measures(filename, measures, cores):
	final_measures = OrderedDict()
	final_measures['Benchmark'] = filename.split('.')[1]

	for x in measures:
		if 'System' in x[0]:
			final_measures[x[0] + '_' + x[1]] = np.mean(measures[x])
	for x in cores:
		final_measures['Cores_' + x] = np.mean(cores[x])
	final_measures['Vcpus'] = float(filename.split('-')[1].split('.')[0])

	return final_measures

def read_pcm_file(filename, directory):
	measures = pcm_measures(filename, directory)
	cleanup_keys(measures)
	cores = cores_accumulate(measures)
	return finalize_measures(filename, measures, cores)

''' 36   37  38   39    40     41     42    43    44    45    46    47  48  49     50     51     52     53     54
    EXEC,IPC,FREQ,AFREQ,L3MISS,L2MISS,L3HIT,L2HIT,L3MPI,L2MPI,L3OCC,LMB,RMB,C0res%,C1res%,C3res%,C6res%,C7res%,TEMP'''

########################################## PQOS Parser ############################################

def read_pqos_files(pqos_file):
	pqos_f = open(perf_directory + 'pqos/' + pqos_file, 'r')
	rd = csv.reader(pqos_f)
	pqos_measures = dict()
	for row in rd:
		if row[0] == 'Time':
			events = map(lambda x: x.lower(), row[2:])
			for event in events:
				pqos_measures[event] = []
		else:
			measure = row[2:]
			for (i, event) in enumerate(events):
				pqos_measures[event].append(float(measure[i]))
	return pqos_measures

def read_pqos_file(filename, directory):
	with open(directory + filename) as csvf:
		name = filename.split('.')[1]
		vcpus = float(name.split('-')[1])
		rowread = csv.reader(csvf, delimiter=',')
		(ipc, misses, llc, mbl, mbr, n) = (0, 0, 0, 0, 0, 0)
		measures = [0, 0, 0, 0, 0, 0]
		for row in rowread:
			if row[0] == 'Time':
				continue
			instance = map(float, row[2:] + [1])
			measures = map(add, measures, instance)
		measures = map(lambda x: x / measures[-1], measures)
		csvf.close()
	return [filename.split('.')[1]] + measures[:-1] + [vcpus]

########################################## Perf Parser ############################################

def read_perf_file(filename, directory):
	measures = OrderedDict()
	with open(directory + filename) as perf_f:
		name = filename.split('.')[1]
		line = perf_f.readline()
		while line:
			tokens = line.split()
			if len(tokens) == 0 or tokens[0] == '#' or '<not' in tokens:
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
			#measures[event] = np.mean(measures[event])
			measures[event] = gmean(list(filter(lambda x: x > 0, measures[event])))

def perf_to_csv(measures, name):
	out_file = open(csv_dir + 'perf_csv/' + name + '_perf.csv', 'w')
	writer = csv.writer(out_file)
	events = measures.keys()
	writer.writerow(events)
	for i in range(max(map(len, measures.values()))):
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
		measures['branch-misses'] = map(lambda x: (float(x[0]) / x[1]) if x[1] > 0 else 0,
									list(zip(measures['branch-misses'], measures['branch-instructions'])))
		measures['dTLB-misses'] = map(sum, list(zip(measures['dTLB-load-misses'], measures['dTLB-store-misses'])))
		measures.pop('dTLB-load-misses')
		measures.pop('dTLB-store-misses')
		for event in [x for x in measures if 'miss' in x and 'branch' not in x]:
			measures[event] = map(lambda x: (x[0] * 1000.0 / x[1]) if x[1] > 0 else 0,
									list(zip(measures[event], measures['instructions'])))
		measures.pop('branch-instructions')
		measures.pop('instructions')

def attach_pqos(all_measures):
	pqos_files = os.listdir(perf_directory + 'pqos/')
	for pqos_file in pqos_files:
		pqos_f = open(perf_directory + 'pqos/' + pqos_file, 'r')
		rd = csv.reader(pqos_f)
		pqos_measures = dict()
		for row in rd:
			if row[0] == 'Time':
				events = map(lambda x: x.lower(), row[2:])
				for event in events:
					pqos_measures[event] = []
			else:
				measure = row[2:]
				for (i, event) in enumerate(events):
					pqos_measures[event].append(float(measure[i]))
		for event in pqos_measures:
			all_measures[pqos_file.split('.')[1]][event] = pqos_measures[event]

############################################# Main ################################################

def perf_files(tool = 'pqos'):
	version = ''
	if len(tool.split('-')) == 2:
		(tool, version) = tool.split('-')
	directory = perf_directory + tool + ('-' + version if version != '' else '') + '/'
	files = os.listdir(directory)
	all_measures = dict()
	if tool == 'pqos':
		all_measures['Title'] = ['Benchmark', 'IPC', 'LLC_Misses', 'LLC', 'MBL', 'MBR', 'Vcpus', 'Class']
		for f in files:
			bench = f.split('.')[1]
			measures = read_pqos_files(f)
			for event in measures:
				measures[event] = np.mean(measures[event])
			all_measures[bench] = [bench] + measures.values() + [int(bench.split('-')[1])]
			break
	elif tool == 'pcm':
		for f in files:
			m = read_pcm_file(f, directory)
			if 'Title' not in all_measures:
				all_measures['Title'] = m.keys() + ['Class']
			all_measures[m['Benchmark']] = m.values()
	elif tool == 'perf':
		final_title = []
		for f in files:
			measures = read_perf_file(f, directory)
			if final_title == []: final_title = measures.keys()
			elif final_title != measures.keys(): print("Title error on:", f)
			all_measures[f.split('.')[1]] = measures
		if version == '':
			attach_pqos(all_measures)
			mpki_calculation(all_measures)
			apply_mean(all_measures)
			for bench in all_measures:
			#	perf_to_csv(all_measures[bench],bench)
				final_title = list(all_measures[bench].keys())
				all_measures[bench] = [bench] + list(all_measures[bench].values())
			all_measures['Title'] = ['Benchmark'] + final_title + ['Class']
		elif version == 'sp':
			apply_mean(all_measures)
			for bench in all_measures:
				all_measures[bench].pop('instructions')
				final_title = list(all_measures[bench].keys())
				all_measures[bench] = [bench] + list(all_measures[bench].values())
			all_measures['Title'] = ['Benchmark'] + final_title + final_title + ['Slowdown']
	return all_measures

if __name__ == '__main__':
	measures = perf_files(sys.argv[1])
	pprint.pprint(measures)
	pprint.pprint(measures['Title'])
