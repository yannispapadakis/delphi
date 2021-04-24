from base_config import *

def read_file(filename, vm_output, vm_perfs, vm_event_times, vms_boot_time, gold_vms, vms_hosts, \
			  vms_names, vms_cost_function, vms_vcpus, vm_times_completed, vm_uuid, \
			  est_profit, vm_times_str, vm_esd, vm_esd_reports):
	fp = open(filename)
	excluded = []
	line = fp.readline()
	limit_heartbeats = 0
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

				# Reports
				if event_type == "internal-profit-report":
					hostname = json_data['hostname']
					value = float(json_data['profit-value'])
					if hostname not in est_profit:
						est_profit[hostname] = [value]
					else:
						est_profit[hostname].append(value)
					line = fp.readline()
					continue
				if event_type == "internal-esd-report":
					esd_dict = json_data['values']
					for (vmid, esd_per_vcpu) in esd_dict.items():
						if vmid not in vm_esd:
							vm_esd[vmid] = tuple([[x] for x in esd_per_vcpu])
						else:
							for vcpu in vm_esd[vmid]:
								vcpu.append(esd_per_vcpu[vm_esd[vmid].index(vcpu)])
						if vmid not in vm_esd_reports:
							vm_esd_reports[vmid] = [event_epoch]
						else:
							vm_esd_reports[vmid].append(event_epoch)
					line = fp.readline()
					continue
				if event_type == "acticloud-external-openstack-filter-profit-report":
					line = fp.readline()
					continue

				vm_seq_num = json_data['vm_seq_num']
				if vm_seq_num in excluded:
					line=fp.readline()
					continue
				if event_type == "boot":
					vm_perfs[vm_seq_num] = []
					vm_uuid[vm_seq_num] = json_data['vm_uuid']
					vm_event_times[vm_seq_num] = []
					vm_event_times[vm_seq_num].append(event_epoch)
					vm_times_completed[vm_seq_num] = 0
					vms_boot_time[vm_seq_num] = event_epoch
					vm_times_str[vm_seq_num] = [event_str]
				elif event_type == "shutdown":
					limit_heartbeats = 1
				elif event_type == "spawn":
					vcpus = json_data['vcpus']
					vms_vcpus[vm_seq_num] = vcpus
					vm_output[vm_seq_num] = []
					host = json_data['host']
					vms_hosts[vm_seq_num] = host
				elif event_type == "heartbeat":
					if limit_heartbeats == 2:
						line = fp.readline()
						continue
					if limit_heartbeats == 1: limit_heartbeats = 2
					vm_times_completed[vm_seq_num] += 1
					bench = json_data['bench']
					load = 0 if bench != "stress-cpu" else json_data['load']
					output = json_data['output']
					vcpus = json_data['vcpus']
					output_lines = output.split(';')
					perf = 0.0
					base_perf = 1.0
					if "stress-cpu" in bench:
						try:
							perf_line = output_lines[4]
						except:
							if vm_seq_num not in excluded:
								excluded.append(vm_seq_num)
							line = fp.readline()
							continue
						base_perf = STRESS_CPU_ISOLATION[vcpus][load]
						perf = float(perf_line.split()[8])
					elif "stress-stream" in bench:
						first_perf_line_index = 4
						base_perf = STRESS_STREAM_ISOLATION[vcpus]
						perf_sum = 0.0
						for j in range(vcpus):
							try:
								perf_line = output_lines[first_perf_line_index + j]
							except:
								if vm_seq_num not in excluded:
									excluded.append(vm_seq_num)
								break
							if len(perf_line) < 7:
								if vm_seq_num not in excluded:
									excluded.append(vm_seq_num)
								break
							perf = float(perf_line.split()[6])
							perf_sum += perf
						if vm_seq_num in excluded:
							line = fp.readline()
							continue
						perf = perf_sum / vcpus
					elif "spec-" in bench:
						spec_name = bench.split("-")[1]
						base_perf = SPEC_ISOLATION[spec_name][vcpus]
						seconds_sum = 0.0
						seconds_samples = 0
						seconds_list = list()
						for l in output_lines:
							if 'seconds' in l:
								seconds_list.append(int(l.split()[0]))
								seconds_sum += int(l.split()[0])
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

					if not "spec-" in bench: ## Spec is fixed above
						perf = perf / base_perf
					if perf == 0:
						if vm_seq_num not in excluded:
							excluded.append(vm_seq_num)
						line = fp.readline()
						continue
					vm_perfs[vm_seq_num].append(perf if perf > 1 else 1.0)
					vm_event_times[vm_seq_num].append(event_epoch)
					vm_times_str[vm_seq_num].append(event_str)

			except ValueError:
				pass
		elif "Spawned new VM" in line:
			tokens = line.split()
			vm_seq_num = int(tokens[9])
			vm_name = tokens[12]
			vms_cost_function[vm_seq_num] = True
			if "gold" in vm_name:
				gold_vms.append(vm_seq_num)
			elif "to_completion" in vm_name:
				vms_cost_function[vm_seq_num] = False
			vms_names[vm_seq_num] = vm_name
		elif "Workload file:" in line:
			workload_file = line.split()[7]

		line = fp.readline()
	fp.close()
	dicts = [vms_names, vm_perfs, vm_event_times, vms_boot_time, vms_hosts, vms_cost_function, vms_vcpus, vm_times_completed]
	for vm_seq_num in vms_names:
		try:
			perf_test = vm_perfs[vm_seq_num]
			event_times_test = vm_event_times[vm_seq_num]
			boot_time_test = vms_boot_time[vm_seq_num]
			hosts_test = vms_hosts[vm_seq_num]
			cost_function_test = vms_cost_function[vm_seq_num]
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

def perf_and_income(vm_perfs, vm_names, vms_cost_function, gold_vms, vm_total, vm_event_times, \
					vms_vcpus, vm_mean_perf, vm_times_completed):
	for vm in vm_names:
		name = vm_names[vm]
		times = vm_times_completed[vm]
		tokens = name.split('-')
		time_axis = vm_event_times[vm]
		if len(time_axis) == 1:
			vm_mean_perf[vm] = 1
			vm_total[vm] = 0
			continue
		if vm_perfs[vm] == []:
			print("EMPTY LIST OF PERFS: ", vm)
		vcpus = vms_vcpus[vm]
		duration = time_axis[-1] - time_axis[0]
		duration_mins = duration / 60.0
		if 'to_completion' in tokens:
			spec_name = tokens[3]
			base_time = SPEC_ISOLATION[spec_name][vcpus]
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

		if vms_cost_function[vm]:
			vm_total[vm] = userfacing(vm in gold_vms, vm_mean_perf[vm]) * duration_mins * vcpus
		else:
			vm_total[vm] = batch(vm_mean_perf[vm]) * duration_mins * vcpus
		
def isolation_income(vms_names, vms_vcpus, vm_total_opt, vm_times_completed):
	for vm in vms_names:
		name = vms_names[vm]
		vcpus = vms_vcpus[vm]
		tokens = name.split('-')
		is_gold = tokens[1] == 'gold'
		if 'stress' in tokens:
			time = tokens[6] if 'cpu' in tokens else tokens[5]
			rate = userfacing(is_gold, 1.0)
			vm_total_opt[vm] = rate * int(time) * vcpus
		if 'spec' in tokens:
			spec_name = tokens[3]
			base_time = SPEC_ISOLATION[spec_name][vcpus]
			times = vm_times_completed[vm]
			time = (times * base_time) / 60.0
			rate = userfacing(is_gold, 1.0) if is_gold else batch(1.0)
			vm_total_opt[vm] = rate * time * vcpus



def parse_files(ld = pairs_dir, endswith = '.txt'):
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
		vms_hosts = dict()
		vms_names = dict()
		vms_cost_function = dict()
		vms_vcpus = dict()
		vm_times_completed = dict()
		vm_total = dict()
		vm_total_opt = dict()
		vm_mean_perf = dict()
		vm_uuid = dict()
		est_profit = dict()
		vm_output = dict()
		vm_times_str = dict()
		vm_esd = dict()
		vm_esd_reports = dict()
			
		try:
			ret = read_file(ld + filename, vm_output, vm_perfs, vm_event_times, vms_boot_time, \
						gold_vms, vms_hosts, vms_names, vms_cost_function, vms_vcpus, \
						vm_times_completed, vm_uuid, est_profit, vm_times_str, vm_esd,\
						vm_esd_reports)
		except:
			print("Error in:", filename)
			return {}
		if ret[0] != '0':
			failures.append(ret)
		perf_and_income(vm_perfs, vms_names, vms_cost_function, gold_vms, vm_total, vm_event_times, \
						vms_vcpus, vm_mean_perf, vm_times_completed)
		isolation_income(vms_names, vms_vcpus, vm_total_opt, vm_times_completed)
		dicts = {'vm_perfs': vm_perfs, 'vm_event_times': vm_event_times, 'gold_vms':gold_vms, \
				 'vms_boot_time': vms_boot_time, 'vms_hosts': vms_hosts, 'vms_names': vms_names, \
				 'vms_cost_function': vms_cost_function, 'vms_vcpus': vms_vcpus, \
				 'vm_total': vm_total, 'vm_total_opt': vm_total_opt, 'vm_output': vm_output, \
				 'vm_mean_perf': vm_mean_perf, 'vm_times_completed': vm_times_completed, \
				 'vm_times_str': vm_times_str, 'vm_uuid': vm_uuid, 'vm_esd': vm_esd, \
				 'vm_esd_reports': vm_esd_reports}
		if est_profit:
			dicts['est_profit'] = est_profit
		total_measures[filename] = dicts

	if failures == []:
		pass #print "Parsed all files successfully in dir:", ld
	else:
		for f in failures:
			print("From file: " + f[0] + "\n\tVMs removed: " + str(f[1]))
	return total_measures

#total_measures = parse_files()
