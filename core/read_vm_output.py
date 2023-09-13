from benchmarks import *

def read_file(filename, vm_output, vm_perfs, vm_event_times, vms_boot_time, gold_vms, \
			  vms_names, vms_vcpus, vm_times_completed, vm_uuid, vm_times_str):
	fp = open(filename)
	excluded = []
	line = fp.readline()
	limit_hb = []
	while line:
		tokens = line.split(" - ")
		if "EVENT" in line:
			try:
				event_data = tokens[2].replace("EVENT: ", "")
				json_data = json.loads(event_data)
				if not 'event' in json_data:
					line = fp.readline()
					continue
				event_type = json_data['event']
				event_str = json_data['time']
				event_time = datetime.datetime.strptime(json_data['time'], "%Y-%m-%d.%X")
				event_epoch = int(event_time.strftime("%s"))

				vm_seq_num = json_data['vm_seq_num']
				if len(limit_hb) <= vm_seq_num: limit_hb.append(0)
				gold_vms.append(vm_seq_num)
				if vm_seq_num in excluded:
					line=fp.readline()
					continue
				if event_type == "boot":
					vm_perfs[vm_seq_num] = []
					vm_uuid[vm_seq_num] = json_data['vm_uuid']
					vm_event_times[vm_seq_num] = [event_epoch]
					vm_times_completed[vm_seq_num] = 0
					vms_boot_time[vm_seq_num] = event_epoch
					vm_times_str[vm_seq_num] = [event_str]
					vm_output[vm_seq_num] = []
					filename_backup = filename
					filename = filename.replace("img-dnn", "imgdnn").replace("tailbench.", "")
					try: vms_vcpus[vm_seq_num] = int(filename.split('/')[-1].split('.')[0].split('-')[vm_seq_num][-1])
					except: vms_vcpus[vm_seq_num] = 2
					filename = filename_backup
				elif event_type == "shutdown":
					limit_hb[vm_seq_num] = 1
				elif event_type == "spawn":
					vms_vcpus[vm_seq_num] = json_data['vcpus']
				elif event_type == "heartbeat":
					if limit_hb[vm_seq_num] == 2:
						line = fp.readline()
						continue
					if limit_hb[vm_seq_num] == 1 and "tailbench" not in vms_names[vm_seq_num]: limit_hb[vm_seq_num] = 2
					vm_times_completed[vm_seq_num] += 1
					vm_event_times[vm_seq_num].append(event_epoch)
					bench = json_data['bench']
					try:
						vms_names[vm_seq_num]
					except:
						vm_name = bench.replace('.','-') if 'parsec' in bench else bench
						vm_name = 'acticloud1-gold-' + vm_name
						vms_names[vm_seq_num] = vm_name
					output = json_data['output']
					vcpus = json_data['vcpus']
					output_lines = output.split(';')
					perf = 0.0
					base_perf = 1.0
					if "spec-" in bench or "parsec" in bench:
						spec_name = bench.split("-")[0]
						if "spec-" in bench: spec_name = bench.split("-")[1]
						try:
							base_perf = benches_vcpus[spec_name]['runtime_isolation'][vcpus]
						except:
							base_perf = benches_vcpus['spec-' + spec_name]['runtime_isolation'][vcpus]
						seconds_sum = 0.0
						seconds_samples = 0
						seconds_list = list()
						for l in output_lines:
							if 'seconds' in l:
								seconds_list.append(float(l.split()[0]))
								seconds_sum += float(l.split()[0])
								seconds_samples += 1
						if seconds_samples == 0:
							if vm_seq_num not in excluded:
								excluded.append(vm_seq_num)
							line = fp.readline()
							continue
						if seconds_sum == 0:
							if vm_seq_num not in excluded:
								excluded.append(vm_seq_num)
							line = fp.readline()
							continue
						vm_output[vm_seq_num].append(tuple(seconds_list))
						perf = (seconds_sum / seconds_samples) / base_perf
					elif "tailbench" in bench:
						tail_name = bench.replace("img-dnn", "imgdnn").split('-')[0].replace("imgdnn", "img-dnn")
						base_perf = benches_vcpus[tail_name]['p95' if p95 else 'p99'][vcpus]
						latency = float(output_lines[1].split(' | ')[1 - int(p95)].split()[1])
						vm_output[vm_seq_num].append(latency)
						perf = latency / base_perf
					if perf == 0:
						if vm_seq_num not in excluded:
							excluded.append(vm_seq_num)
						line = fp.readline()
						continue
					vm_perfs[vm_seq_num].append(perf if perf > 1 else 1.0)
					vm_times_str[vm_seq_num].append(event_str)

			except:
				pass
		elif "Spawned new VM" in line:
			tokens = line.split()
			vm_seq_num = int(tokens[9])
			vm_name = tokens[12]
			if "gold" in vm_name:
				gold_vms.append(vm_seq_num)
			vms_names[vm_seq_num] = vm_name

		line = fp.readline()
	fp.close()
	dicts = [vms_names, vm_perfs, vm_event_times, vms_boot_time, vms_vcpus, vm_times_completed]
	for vm_seq_num in vms_names:
		try:
			perf_test = vm_perfs[vm_seq_num]
			event_times_test = vm_event_times[vm_seq_num]
			boot_time_test = vms_boot_time[vm_seq_num]
			vcpus_test = vms_vcpus[vm_seq_num]
			times_completed_test = vm_times_completed[vm_seq_num]
		except KeyError:
			excluded.append(vm_seq_num)
	for vm_seq_num in excluded:
		for d in dicts:
			if vm_seq_num in d:
				del d[vm_seq_num]

	if len(excluded):
		return (filename, excluded)
	else:
		return ('0',[])

def mean_perf_calc(vm_perfs, vm_names, vm_event_times, \
					vms_vcpus, vm_mean_perf, vm_times_completed):
	for vm in vm_names:
		name = vm_names[vm]
		times = vm_times_completed[vm]
		tokens = name.replace("img-dnn", "imgdnn").split('-')
		time_axis = vm_event_times[vm]
		if len(time_axis) == 1:
			vm_mean_perf[vm] = 1
			continue
		if vm_perfs[vm] == []:
			print("List of perfs is empty for vm_seq_num:", vm)
			print(vm_names, vms_vcpus)
			continue
		vcpus = vms_vcpus[vm]
		duration = time_axis[-1] - time_axis[0]
		duration_mins = duration / 60.0
		if 'to_completion' in tokens:
			spec_name = tokens[2 if "tailbench" in name else 3]
			if 'parsec.' in name or "img-dnn" in name: spec_name = tokens[2].replace("imgdnn", "img-dnn")
			if "tailbench" in spec_name:
				base_time = benches_vcpus[spec_name]['p95' if p95 else 'p99'][vcpus]
				vm_mean_perf[vm] = np.mean(vm_perfs[vm])
			else:
				try:
					search = spec_name if 'parsec.' in name else 'parsec.' + spec_name
					base_time = benches_vcpus[search]['runtime_isolation'][vcpus]
				except:
					base_time = benches_vcpus['spec-' + spec_name]['runtime_isolation'][vcpus]
				duration = sum([base_time * x for x in vm_perfs[vm]])
				duration_mins = duration / 60.0
				vm_mean_perf[vm] = min(duration / (base_time * times), np.mean(vm_perfs[vm]))
		else:
			weighted_perfs = []
			for t1 in time_axis[1:]:
				prev_idx = time_axis.index(t1) - 1
				t0 = time_axis[prev_idx]
				dt = t1 - t0
				weighted_perfs.append((t1 - t0) * vm_perfs[vm][prev_idx])
			vm_mean_perf[vm] = sum(weighted_perfs) / duration

def parse_files(ld = coexecutions_dir, endswith = '.txt'):
	files = [f for f in os.listdir(ld) if f.endswith(endswith)]
	if files == []:
		print("No files found with given pattern in dir: ", ld)
		return None
	files.sort(reverse=True)

	total_measures = OrderedDict()
	failures = []
	for filename in files:
		vm_perfs = dict()
		vm_event_times = dict()
		gold_vms = []
		vms_boot_time = dict()
		vms_names = dict()
		vms_vcpus = dict()
		vm_times_completed = dict()
		vm_mean_perf = dict()
		vm_uuid = dict()
		vm_output = dict()
		vm_times_str = dict()
			
		try:
			ret = read_file(ld + filename, vm_output, vm_perfs, vm_event_times, vms_boot_time, \
						gold_vms, vms_names, vms_vcpus, vm_times_completed, vm_uuid, vm_times_str)
		except:
			print("Error in:", filename)
			return {}
		if ret[0] != '0':
			failures.append(ret)
		mean_perf_calc(vm_perfs, vms_names, vm_event_times, vms_vcpus, vm_mean_perf, vm_times_completed)
		dicts = {'vm_perfs': vm_perfs, 'vm_event_times': vm_event_times, \
				 'vms_boot_time': vms_boot_time, 'vms_names': vms_names, \
				 'vms_vcpus': vms_vcpus, 'vm_output': vm_output, \
				 'vm_mean_perf': vm_mean_perf, 'vm_times_completed': vm_times_completed, \
				 'vm_times_str': vm_times_str, 'vm_uuid': vm_uuid}
		total_measures[filename] = dicts
	for f in failures:
		print("From file: " + f[0] + "\n\tVMs removed: " + str(f[1]))
	return total_measures
