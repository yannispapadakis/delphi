import os, csv, sys
import numpy as np
from collections import OrderedDict
from operator import add

########################################### PCM Parser ###########################################

perf_directory = '/home/ypap/characterization/perf_runs/results/'

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

import pprint
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
		for event in measures:
			measures[event] = np.mean(measures[event])
		perf_f.close()
	return ([name] + measures.values(), ['Bench'] + measures.keys())

############################################# Main ################################################

def perf_files(tool = 'pqos'):
	directory = perf_directory + tool + '/'
	files = os.listdir(directory)
	all_measures = dict()
	if tool == 'pqos':
		all_measures['Title'] = ['Benchmark', 'IPC', 'LLC_Misses', 'LLC', 'MBL', 'MBR', 'Vcpus', 'Class']
		for f in files:
			all_measures[f.split('.')[1]] = read_pqos_file(f, directory)
	elif tool == 'pcm':
		for f in files:
			m = read_pcm_file(f, directory)
			if 'Title' not in all_measures:
				all_measures['Title'] = m.keys() + ['Class']
			all_measures[m['Benchmark']] = m.values()
	elif tool == 'perf':
		final_title = []
		for f in files:
			(measures, title) = read_perf_file(f, directory)
			if final_title == []: final_title = title
			elif final_title != title: print "Title error on:", f
			all_measures[f.split('.')[1]] = measures
		all_measures['Title'] = final_title + final_title[1:] + ['Slowdown']
	return all_measures

if __name__ == '__main__':
	measures = perf_files(sys.argv[1])
	pprint.pprint(measures)
