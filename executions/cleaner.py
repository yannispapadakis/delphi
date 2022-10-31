#!/usr/bin/python
import sys
sys.path.append("../core/")
from benchmarks import *

def clean(filename):
	fp = open(filename)
	fw = open("output.txt", mode='w')
	line = fp.readline()
	(ssh_fail, tail_failed, tail_total, parsec_failed, disk_failed) = (0, 0, 0, 0, 0)
	tail_exists = False
	(hb_expected, hb_completed, bench_expected) = (dict(), dict(), dict())
	report = []
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
		if "Spawned new VM" in line:
			hb_expected[int(tokens[2].split()[5])] = int(tokens[2].split()[-1].split('-')[-2].split('_')[0])
			bench_expected[int(tokens[2].split()[5])] = tokens[2].split()[-1].split('-')[-3].split('.')[-1]
			tail_exists = "tailbench" in line or tail_exists
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
				if "lats.bin_error" in event_data or "RuntimeWarning" in event_data:
					tail_failed += 1
					line = fp.readline()
					continue
			if "heartbeat" in line:
				json_data = json.loads(event_data)
				if bench_expected[json_data['vm_seq_num']] not in json_data["bench"]:
					report.append(json_data["bench"] + " heartbeat found in " + filename)
				else:
					if json_data['vm_seq_num'] in hb_completed:
						hb_completed[json_data['vm_seq_num']] += 1
					else: hb_completed[json_data['vm_seq_num']] = 1
		fw.write(line)
		line = fp.readline()
	fp.close()
	fw.close()
	os.rename('output.txt', filename)
	for vm in hb_completed:
		if hb_expected[vm] > hb_completed[vm]:
			print(str(hb_completed[vm]) + '/' + str(hb_expected[vm]) + " executions of VM: " + str(vm) + " (" + filename.split('/')[-1] + ")")
	if '/' in filename:
		dir_fn = filename.split('/')
		(dir_, filename) = ('/'.join(dir_fn[:-1] + ['']), dir_fn[-1])
	if tail_exists and tail_failed == tail_total: report.append("All executions failed in: " + filename)
	if parsec_failed > 0: report.append("At least one execution returned empty output in: " + filename)
	if disk_failed > 0: report.append("Disk had no space in: " + filename)
	if ssh_fail > 0: report.append("Multiple SSH processes in: " + filename)
	if report != []:
		for r in report: print r
		dest = results_dir + 'trash/'
		os.rename(dir_ + filename, dest + filename)
	else:
		fn_fix = filename.replace('img-dnn', 'imgdnn')
		(b1, v1, b2, v2) = [y for x in list(map(lambda x: x.split('_'), fn_fix.split('.txt')[0].split('-'))) for y in x]
		(b1, b2) = (b1.replace('imgdnn', 'img-dnn'), b2.replace('imgdnn', 'img-dnn'))
		dest = coexecutions_dir + b1 + '/' + v1 + 'vs' + v2 + '/'
		os.rename(dir_ + filename, dest + filename)
		if filename in os.listdir(results_dir + 'trash/'): os.remove(results_dir + 'trash/' + filename)

def files_at_results(benchmarks):
	if benchmarks == []:
		benchmarks = set(map(lambda x: x.split("_")[0], map(lambda x: x.split('-')[0], filter(lambda x: x.endswith('.txt') and not x.startswith('internal'), os.listdir(results_dir)))))
	for bench in benchmarks:
		try: files = subprocess.check_output("ls " + results_dir + bench + "*-*txt", shell=True)
		except:
			print("No runs for benchmark:", bench)
			continue
		for f in list(filter(lambda x: x != '', files.split('\n'))): clean(f)

def parse_all_files(folders):
	benchmarks = subprocess.check_output('ls -rt ' + coexecutions_dir, shell = True).split("\n")[28:-1]
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
	if sys.argv[1] == 'dir':
		parse_all_files(sys.argv[2:])
	else: files_at_results(sys.argv[1:])
