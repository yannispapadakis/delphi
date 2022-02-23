#!/usr/bin/python3
from pairing import *

matrix_dir = home_dir + 'results/'

def get_predictions_mult(benchmarks):
	predictions = dict()
	classes = 2
	real = True
	slos = sorted(list(set(map(float, map(lambda x: x.split('_')[1], benchmarks)))))
	features = ['sens', 'cont']
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
	ans = dict((i + '.' + x.split('_')[0], 
		{'slo': float(x.split('_')[1]),
	     'sens': int(predictions[float(x.split('_')[1])]['sens'][x.split('_')[0]]),
		 'cont': dict((i, int(predictions[i]['cont'][x.split('_')[0]])) for i in slos)}) \
		 for (i, x) in map(lambda y: y.split(':'), benchmarks))
	return ans

def exhaustive_matrix(preds):
	benchmarks = list(preds.keys())
	for row in preds:
		preds[row]['heatmap'] = dict()
		for col in set(benchmarks).difference([row]):
			deny = (preds[row]['sens'] and preds[col]['cont'][preds[row]['slo']]) or \
				   (preds[col]['sens'] and preds[row]['cont'][preds[col]['slo']])
			preds[row]['heatmap'][col] = ((preds[row]['sens'], preds[col]['cont'][preds[row]['slo']]), deny)

def print_matrix(preds, workload):
	out_file = matrix_dir + workload + '_matrix.csv'
	fd = open(out_file, mode='w')
	writer = csv.writer(fd, delimiter='\t')
	benchmarks = list(preds.keys())
	writer.writerow([''] + benchmarks)
	for bench1 in benchmarks:
		print_line = [bench1]
		for bench2 in benchmarks:
			try:
				print_line.append(preds[bench1]['heatmap'][bench2][0])
			except:
				print_line.append('0')
		writer.writerow(print_line)
	fd.close()

def sort_benchmarks(preds):
	queue = sorted(list(preds.items()), key = lambda x: x[1]['slo'], reverse = True)
	queue = sorted(queue, key = lambda x: sum(x[1]['cont'].values()), reverse = True)
	queue = sorted(queue, key = lambda x: x[1]['sens'], reverse = True)
	queue = sorted(queue, key = lambda x: sum(map(lambda y: y[1], x[1]['heatmap'].values())), reverse = True)
	return queue

def wont_find_candidate(queue):
	total_cand_list = []
	for (i, bench) in enumerate(queue):
		candidate_list = list(map(lambda x:x[0], filter(lambda y: y[1][1] == 0, bench[1]['heatmap'].items())))
		total_cand_list = list(set(total_cand_list + candidate_list))
		if len(total_cand_list) < i + 1:
			return i
	return -1

def bad_pairing(queue):
	pairs = []
	error_index = wont_find_candidate(queue)
	while error_index > -1:
		error_bench = queue.pop(error_index)
		bench_to_pair = queue.pop(0)
		pairs.append((error_bench[0], bench_to_pair[0]))
		error_index = wont_find_candidate(queue)
	return (pairs, queue)

def multSLOs(benchmarks, workload):
	preds = get_predictions_mult(benchmarks)
	exhaustive_matrix(preds)
	queue = sort_benchmarks(preds)
	(pairs, queue) = bad_pairing(queue)
	for bench in queue:
		flatpairs = [x for pair in pairs for x in pair]
		if bench[0] in flatpairs: continue
		valid_candidates = list(filter(lambda y: y[1][1] == 0 and y[0] not in flatpairs, bench[1]['heatmap'].items()))
		if len(valid_candidates) == 0:
			print("There are no valid candidates for:", bench[0])
			return
		# bench's sensitivity
		combinations = sorted(list(set(map(lambda y: y[1][0], valid_candidates))), key = lambda y: sum(y), reverse = True)
		chosen_combination = combinations[0]
		sens_candidates = list(map(lambda z: z[0], filter(lambda y: y[1][0] == chosen_combination, valid_candidates)))
		# candidate's sensitivity
		sens_of_candidates = sorted([(cand, preds[cand]['heatmap'][bench[0]][0]) for cand in sens_candidates], key = itemgetter(1), reverse = True)
		chosen_combination_2 = sens_of_candidates[0][1]
		sens_of_candidates = list(map(lambda y: y[0], filter(lambda x: x[1] == chosen_combination_2, sens_of_candidates)))
		pred_candidates = list(filter(lambda x: x[0] in sens_of_candidates, preds.items()))
		pred_candidates = sorted(pred_candidates, key = lambda x: x[1]['slo'])
		pred_candidates = sorted(pred_candidates, key = lambda x: sum(x[1]['cont'].values()), reverse = True)
		pred_candidates = sorted(pred_candidates, key = lambda x: sum(map(lambda y: y[1], x[1]['heatmap'].values())), reverse = True)
		pair = pred_candidates[0]
		pairs.append((bench[0], pair[0]))
	pprint.pprint(pairs)
	return preds

def helper_print(queue, preds):
	candidates_per_bench = dict((bench, sum(map(lambda x: x[1], preds[bench]['heatmap'].values()))) for bench in preds)
	for x in queue:
		print(x[0], '\t', candidates_per_bench[x[0]], '\t', x[1]['sens'], '\t', x[1]['cont'], '\t', x[1]['slo'])

def workload_reader(bench_file):
	fd = open(bench_file)
	reader = csv.reader(fd, delimiter=',')
	benchmarks = [str(i) + ':' + row[0] + '-' + row[1] + '_' + row[2] for (i, row) in enumerate(reader)]
	fd.close()
	return benchmarks

def help_message(ex):
	m =  "Usage:    %s <workload>\n" % ex
	m += "Workload: " + ' | '.join(list(map(lambda x: x.split('.')[0], filter(lambda x: x.endswith('multSLO.csv'), os.listdir('workload_pairs/'))))) + '\n'
	print(m)

if __name__ == '__main__':
	if len(sys.argv) < 2: help_message(sys.argv[0])
	else: preds = multSLOs(workload_reader(wd_dir + sys.argv[1]), sys.argv[1].split('.')[0])
