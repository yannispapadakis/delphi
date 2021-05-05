import sys
sys.path.append('../core/')
from read_file import *
from grid import *
import pprint
import csv

# grid
grid = generate_grid()
read_grid(grid)

# predictor
mod = 'SVC'
pred_dir = home_dir + 'results/predictions/' + mod + '/'
features = ['sens', 'cont']
config = ['', '2', '1.2', mod]
suffix = '_'.join(config) + '.csv'

predictions = dict()
for f in features:
	with open(pred_dir + f + suffix, mode='r') as pred:
		reader = csv.reader(pred, delimiter='\t')
		predictions[f] = dict((rows[0], rows[1:]) for rows in reader)
		pred.close()

# measurements from file

total_measures = parse_files()
for filename in total_measures:
	out_file = csv_dir + filename.replace('txt','csv')
	fd = open(out_file, mode='w')
	writer = csv.writer(fd, delimiter='\t')
	measures = total_measures[filename]
	names = map(lambda x: x.split('.')[1].split('-')[0], measures['vms_names'].values())
	print ['Name', 'Mean SD', 'Grid SD', 'Success/Total', 'Whisker', 'Prediction', 'Probabilities']
	for vm in measures['vms_names']:
		current_vm = names[vm] + '-' + str(measures['vms_vcpus'][vm])
		actual_sd = measures['vm_mean_perf'][vm]
		paired_vm = names[vm + 1 if vm % 2 == 0 else vm - 1] + '-' + \
					str(measures['vms_vcpus'][vm + 1 if vm % 2 == 0 else vm - 1])
		grid_sd = grid[current_vm][paired_vm]
		row = [current_vm, float("{:.2f}".format(actual_sd)), float("{:.2f}".format(grid_sd))]
		times_completed = measures['vm_times_completed'][vm]
		success_execs = len([x for x in measures['vm_perfs'][vm] if x < 1.2])
		row.append(str(success_execs) + '/' + str(times_completed))
		prediction = dict((f, predictions[f][current_vm]) for f in predictions)
		for f in prediction:
			whisker = float(prediction[f][2])
			pred = int(prediction[f][0])
			prob = map(int, prediction[f][3:5])
			row += [whisker, pred, prob]
		writer.writerow(row)
		print str(row).replace('[','').replace(']','').replace(', ','\t')
		if vm % 2 > 0:
			writer.writerow(['-----------'])
			print '---------------------'
