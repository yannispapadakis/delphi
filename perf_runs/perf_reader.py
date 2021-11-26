import os, csv, sys
import numpy as np
from scipy.stats.mstats import gmean
from collections import OrderedDict
from operator import add
import pprint
sys.path.append('../core/')
from read_file import *

########################################### PCM Parser ###########################################

perf_directory = '/home/ypap/characterization/results/isolation_runs/'
csv_dir = '/home/ypap/characterization/results/'

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

def read_pqos_files(pqos_file, run_periods):
	pqos_f = open(perf_directory + 'pqos/' + pqos_file, 'r')
	rd = csv.reader(pqos_f)
	pqos_measures = dict()
	for row in rd:
		if row[0] == 'Time':
			events = list(map(lambda x: x.lower(), row[2:]))
			for event in events:
				pqos_measures[event] = []
		else:
			time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours=2)
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
	out_file = open(csv_dir + 'perf_csv/' + name + '_perf.csv', 'w')
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
	pqos_files = os.listdir(perf_directory + 'pqos/')
	for pqos_file in list(filter(lambda x: x.endswith('csv'), pqos_files)):
		bs = ae = alll = 0
		pqos_f = open(perf_directory + 'pqos/' + pqos_file, 'r')
		rd = csv.reader(pqos_f)
		pqos_measures = dict()
		for row in rd:
			if row[0] == 'Time':
				events = list(map(lambda x: x.lower(), row[2:]))
				for event in events:
					pqos_measures[event] = []
			else:
				time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours=2)
				time = int(time.strftime("%s"))
				if time < run_periods[pqos_file.split('.')[1]][0] or time > run_periods[pqos_file.split('.')[1]][1]:
					continue
				measure = row[2:]
				for (i, event) in list(enumerate(events)):
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
		run_periods = time_cleanup('pqos')
		for f in list(filter(lambda x: x.endswith('csv'), files)):
			bench = f.split('.')[1]
			measures = read_pqos_files(f, run_periods[bench])
			for event in measures:
				measures[event] = np.mean(measures[event])
			all_measures[bench] = [bench] + list(measures.values()) + [int(bench.split('-')[1])]
	elif tool == 'pcm':
		for f in files:
			m = read_pcm_file(f, directory)
			if 'Title' not in all_measures:
				all_measures['Title'] = m.keys() + ['Class']
			all_measures[m['Benchmark']] = m.values()
	elif tool == 'perf':
		final_title = []
		run_periods = time_cleanup('perf')
		for f in list(filter(lambda x: x.endswith('csv'), files)):
			measures = read_perf_file(f, directory, run_periods[f.split('.')[1]])
			if final_title == []: final_title = measures.keys()
			elif final_title != measures.keys(): print("Title error on:", f)
			all_measures[f.split('.')[1]] = measures
		if version == '':
			attach_pqos(all_measures)
			mpki_calculation(all_measures)
			apply_mean(all_measures)
			for bench in all_measures:
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

def time_cleanup(tool = 'perf'):
	directory = perf_directory + tool + '/outputs/'
	total_measures = parse_files(directory)
	run_periods = dict()
	for f in total_measures:
		run_periods[f.split('-')[0].replace('_','-')] = (min(total_measures[f]['vm_event_times'][0]), max(total_measures[f]['vm_event_times'][0]))
	return run_periods

if __name__ == '__main__':
	measures = perf_files(sys.argv[1])
