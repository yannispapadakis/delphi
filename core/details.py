from base_config import *
from read_file import *
import pprint

def print_esd(vm, measures):
	print "------------------------------- ESD --------------------------------" 
	uuid = measures['vm_uuid'][vm]
	vm_esd = measures['vm_esd'][uuid]
	vm_perfs = measures['vm_perfs'][vm]
	vm_esd_reports = measures['vm_esd_reports'][uuid]
	vm_event_times = measures['vm_event_times'][vm]
	events = []
	for t1 in vm_event_times:
		for r in vm_esd_reports:
				if r > t1:
					events.append(vm_esd_reports.index(r))
					break
	mean_esd = []
	for i in range(len(events) - 1):
		mean_esd.append(tuple([np.mean(vcpu[events[i]:events[i+1]]) for vcpu in vm_esd]))
	for i in range(len(vm_perfs)):
		print "Execution:", i, "\tPerf:", "{0:.2f}".format(vm_perfs[i]), "|", "ESD:", \
			  ', '.join(["{0:.2f}".format(x) for x in mean_esd[i]])
	print "____________________________________________________________________"

def dettt():
	ans = dict()
	ldir = home_dir + 'results/perf_runs/'
	total_measures = parse_files(ldir)
	for bench in total_measures:
		measures = total_measures[bench]
		nn = bench.split('_')[0]
		if nn not in ans:
			ans[nn] = dict()
		for vm in measures['vms_names']:
			spec_name = measures['vms_names'][vm].split('-')[3]
			vcpus = measures['vms_vcpus'][vm]
			base = SPEC_ISOLATION[spec_name][vcpus]
			output = np.mean(measures['vm_output'][vm])
			ans[nn][vcpus] = output
			#print spec_name + '\t' + str(vcpus) + '\t' + str(base) + '\t' + str(output)
	pprint.pprint(ans)
	return ans


def print_details_of_vm(vm, measures):
	print "------------------------ VM Characteristics ------------------------" 
	spec_name = measures['vms_names'][vm].split('-')[3]
	vcpus = measures['vms_vcpus'][vm]
	base = SPEC_ISOLATION[spec_name][vcpus]
	print "\t\tVM Sequence Number: " + str(vm)
	print "VM Name:", measures['vms_names'][vm]
	print "   uuid:", measures['vm_uuid'][vm]
	print "Base perf:", base, "Cost Function:", "UserFacing" if measures['vms_cost_function'][vm] else "Batch", "vCPUs:", vcpus
	print "Times Completed:", measures['vm_times_completed'][vm]
	print "Output:", measures['vm_output'][vm]
	print "Mean Perf", float("{0:.2f}".format(measures['vm_mean_perf'][vm]))
	tolerate = Billing.gold_tolerate if vm in measures['gold_vms'] else Billing.silver_tolerate
	failed_executions = [(i, float("{0:.2f}".format(x))) for (i,x) in enumerate(measures['vm_perfs'][vm]) if x > tolerate]
	if failed_executions:
		print "\nFailed Executions:\n", failed_executions
		print "Which Started at:"
		print [x for (i,x) in enumerate(measures['vm_times_str'][vm][:-1]) if measures['vm_perfs'][vm][i] > tolerate] 
	print "\nHost:", measures['vms_hosts'][vm]
	print "Income:", measures['vm_total'][vm]
	print "Income in Isolation:", measures['vm_total_opt'][vm]

def print_details(total_measures):
	while True:
		fn = None
		if len(total_measures.keys()) == 1:
			fn = total_measures.keys()[0]
		else:
			print "Choose a file: (index or filename)"
			for (i, filename) in enumerate(total_measures.keys()):
				print "\t" + str(i) + ". " + filename.split('/')[-1]
			fn = raw_input("> ")
		if len(fn) > 3:
			filename = fn
		else:
			filename = total_measures.keys()[int(fn)]
		measures = total_measures[filename]
		while True:
			vms_to_print = raw_input("Which VM? > ")
			if vms_to_print == "":
				continue
			if vms_to_print == "q":
				return
			print_vms = []
			if vms_to_print == "missed":
				print_vms = [vm for vm in measures['gold_vms'] if measures['vm_total'][vm] == 0]
			elif vms_to_print == "gold":
				print_vms = [vm for vm in measures['gold_vms']]
			elif vms_to_print == "all":
				print_vms = [vm for vm in measures['vms_names']]
			else:
				try:
					vm_seq_num = int(vms_to_print)
					name = measures['vms_names'][vm_seq_num]
				except:
					assert False, "Invalid Sequence Number " + vms_to_print
				print_vms = [vm_seq_num]	
			for vm in print_vms:
				print_details_of_vm(vm, measures)
				if "acti" in filename:
					print_esd(vm, measures)
				if len(print_vms) > 1 and print_vms.index(vm) < len(print_vms) - 1:
					next_ = raw_input("")
					if next_ == "q":
						return

def details():
	while True:
		ldir = load_dir + 'pairs/'
		print "Choose benchmark:"
		for (i, x) in enumerate(os.listdir(ldir)):
			print "\t" + str(i) + '. ' + x
		bench = raw_input("> ")
		if bench == "q":
			return
		if bench == "":
			ldir = load_dir
		else:
			if len(bench) < 3:
				bench = os.listdir(ldir)[int(bench)]
			ldir += bench + '/'
			print "Choose combination:"
			for (i, x) in enumerate(os.listdir(ldir)):
				print "\t\t" + str(i) + '. ' + x
			comb = raw_input("> ")
			if len(comb) < 3:
				comb = os.listdir(ldir)[int(comb)]
			ldir += comb + '/'
		print "Entering print_details on dir:", ldir
		print "========================================================="
		total_measures = parse_files(ldir)
		print_details(total_measures)
		cont = raw_input('Next? > ')
		if cont == 'q':
			return

if __name__ == '__main__':
	#dettt()
	details()
