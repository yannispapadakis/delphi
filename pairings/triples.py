#!/usr/bin/python3
from pairing import *

def pred_print():
	s = 1.2
	cl = 2
	version = 'r'
	predictions = dict()
	for f in features:
		with open(get_model(f, cl, s), mode = 'r') as pred_f:
			predictions[f] = dict((rows[0], rows[1 + int(version == 'r')]) for rows in csv.reader(pred_f, delimiter='\t') if rows[0] != 'Bench' and rows[0] != 'Accuracy')

	benches = dict()
	for x in predictions['sens'].keys(): benches[x] = (int(predictions['sens'][x]), int(predictions['cont'][x]))
	return benches

def mult_sd(n):
	benches = pred_print()
	total_measures = parse_files(f"/home/ypap/delphi/results/{n}ads/")

	report = ''
	for f in total_measures.keys():
		benchs = f.split('.txt')[0].split('_')
		perfs = total_measures[f]['vm_mean_perf']
		for (i, bench) in enumerate(benchs):
			report += f"{benches[bench + '-2']}{bench}|{perfs[i]:.3f}|"
			#report += f"{benches[bench + '-2']}{bench}{' ' * (18 - len(bench))}{perfs[i]:.3f}|"
		report+='\n'
	print(report)

if __name__ == '__main__':
	mult_sd(sys.argv[1])
