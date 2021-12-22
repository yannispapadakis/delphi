#!/usr/bin/python3
from pairing import *

def get_predictions_mult(benchmarks):
	predictions = dict()
	classes = 2
	real = True
	slos = sorted(list(set(map(float, map(lambda x: x.split('_')[1], benchmarks)))))
	features = ['sens', 'cont']
	slos = list(set(map(float, [x.split('_')[1] for x in benchmarks])))
	for s in slos:
		predictions[s] = dict()
		for f in features:
			pred_f = open(get_model(f, classes, s), mode = 'r')
			reader = csv.reader(pred_f, delimiter='\t')
			pred = dict((rows[0], rows[-1 if real else 1]) for rows in reader)
			del pred['Bench']
			del pred['Accuracy']
			predictions[s][f] = pred
			pred_f.close()
	ans = dict((x.split('_')[0], 
		{'slo': float(x.split('_')[1]),
	     'sens': int(predictions[float(x.split('_')[1])]['sens'][x.split('_')[0]]),
		 'cont': dict((i, int(predictions[i]['cont'][x.split('_')[0]])) for i in slos)}) \
		 for x in benchmarks)
	pprint.pprint(ans)
	return ans

def multSLOs(benchmarks):
	preds = get_predictions_mult(benchmarks)


def main(args):
	bench_file = wd_dir + args[0]
	fd = open(bench_file)
	reader = csv.reader(fd, delimiter=',')
	benchmarks = [row[0] + '-' + row[1] + '_' + row[2] for row in reader]
	multSLOs(benchmarks)
	fd.close()

def help_message(ex):
	m =  "Usage:    %s <workload>\n" % ex
	m += "Workload: " + ' | '.join(list(map(lambda x: x.split('.')[0], filter(lambda x: x.endswith('multSLO.csv'), os.listdir('workload_pairs/'))))) + '\n'
	print(m)
	return 0

if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.exit(help_message(sys.argv[0]))
	else:
		main(sys.argv[1:])
