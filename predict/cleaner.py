#!/usr/bin/python
import datetime,sys,os,subprocess

def clean(filename):
	fp = open(filename)
	fw = open("output.txt", mode='w')
	line = fp.readline()
	failed = total = 0
	while line:
		tokens = line.split(' - ')
		try:
			time = datetime.datetime.strptime(tokens[0], "%Y-%m-%d.%X")
		except:
			line = fp.readline()
			continue
		if tokens[2].startswith("Something"):
			line = fp.readline()
			continue
		if "EVENT" in line:
			event_data = tokens[2].replace("EVENT: ", "")
			if not event_data.startswith("{"):
				line = fp.readline()
				continue
			if "tailbench" in event_data:
				total += 1
				if "lats.bin_error" in event_data:
					failed += 1
					line = fp.readline()
					continue
		fw.write(line)
		line = fp.readline()
	fp.close()
	fw.close()
	if total > 0 and failed == total:
		print "All executions failed in: " + filename
	os.rename('output.txt', filename)

def parse_all_files(folders):
	coexecutions_dir = '/home/ypap/delphi/results/coexecutions/'
	benchmarks  = subprocess.check_output('ls -rt ' + coexecutions_dir, shell = True).split("\n")[28:-1]
	to_clean = list()
	if len(folders):
		if 'all' in folders: to_clean = benchmarks
		else:
			for bench in folders:
				if bench not in benchmarks:
					folders.pop(folders.index(bench))
			to_clean = folders
	for bench in to_clean:
		for comb in os.listdir(coexecutions_dir + bench):
			ld = coexecutions_dir + bench + '/' + comb
			for filename in os.listdir(ld):
				clean(ld + '/' + filename)
		print bench, "cleaned"
			
if __name__ == "__main__":
	parse_all_files(sys.argv[1:])
