#!/usr/bin/python
import datetime,sys,os,subprocess

def clean(filename):
	fp = open(filename)
	fw = open("output.txt", mode='w')
	line = fp.readline()
	ssh_fail = tail_failed = tail_total = parsec_failed = disk_failed = 0
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
		if "ssh processes" in line:
			ssh_fail += 1
		if "EVENT" in line:
			event_data = tokens[2].replace("EVENT: ", "")
			if not event_data.startswith("{"):
				line = fp.readline()
				continue
			if '"output": ""' in event_data:
				parsec_failed += 1
			if "No space left on device" in event_data:
				disk_failed += 1
			if "tailbench" in event_data:
				tail_total += 1
				if "lats.bin_error" in event_data:
					tail_failed += 1
					line = fp.readline()
					continue
		fw.write(line)
		line = fp.readline()
	fp.close()
	fw.close()
	os.rename('output.txt', filename)
	if '/' in filename:
		dir_fn = filename.split('/')
		(dir_, filename) = ('/'.join(dir_fn[:-1] + ['']), dir_fn[-1])
	if tail_total > 0 and tail_failed == tail_total:
		print "All executions failed in: " + filename
	elif parsec_failed > 0:
		print "At least one execution returned empty output in: " + filename
	elif disk_failed > 0:
		print "Disk had no space in: " + filename
	elif ssh_fail > 0:
		print "Multiple SSH processes in: " + filename
	else:
		fn_fix = filename.replace('img-dnn', 'imgdnn')
		(b1, v1, b2, v2) = [y for x in list(map(lambda x: x.split('_'), fn_fix.split('.txt')[0].split('-'))) for y in x]
		(b1, b2) = (b1.replace('imgdnn', 'img-dnn'), b2.replace('imgdnn', 'img-dnn'))
		dest = '/home/ypap/delphi/results/coexecutions/' + b1 + '/' + v1 + 'vs' + v2 + '/'
		os.rename(dir_ + filename, dest + filename)

def files_at_results(benchmarks):
	for bench in benchmarks:
		files = subprocess.check_output('ls /home/ypap/delphi/results/' + bench + '*-*txt', shell = True)
		for f in list(filter(lambda x: x != '', files.split('\n'))): clean(f)

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
	files_at_results(sys.argv[1:])
#	parse_all_files(sys.argv[1:])
