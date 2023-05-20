#!/usr/bin/python3
from pairing import *

def probabilities(b1, b2, b3):
	def mult_sd(n, preds):
		total_measures = parse_files(f"/home/ypap/delphi/results/{n}ads/")
		results = dict()

		for f in total_measures.keys():
			f = f.replace('img-dnn', 'imgdnn')
			benches = list(map(lambda x: x.replace('_', '-'), f.split('.txt')[0].split('-')))
			benches = list(map(lambda x: x.replace('imgdnn', 'img-dnn'), benches))
			f = f.replace('imgdnn', 'img-dnn')
			perfs = total_measures[f]['vm_mean_perf']
			batch_pred = str(sorted(list(map(lambda x: preds[x], benches))))
			for (i, bench) in enumerate(benches):
				pred = str(preds[bench])
				if pred not in results: results[pred] = {batch_pred: [perfs[i]]}
				else:
					if batch_pred not in results[pred]: results[pred][batch_pred] = [perfs[i]]
					else: results[pred][batch_pred].append(perfs[i])
		return results

	(s, cl) = (1.2, 2)
	predictions = dict()
	for f in features:
		with open(get_model(f, cl, s), mode = 'r') as pred_f:
			predictions[f] = dict((rows[0], rows[2]) for rows in csv.reader(pred_f, delimiter='\t') if rows[0] != 'Bench' and rows[0] != 'Accuracy')
	preds = dict((x, (int(predictions['sens'][x]), int(predictions['cont'][x]))) for x in predictions['sens'].keys())

	triple = [b1, b2, b3]
	violations = []
	probs = []
	for b in triple:
		t = preds[b]
		tr = sorted(list(map(lambda x: preds[x], triple)))
		results = mult_sd(3, preds)[str(t)][str(tr)]
		prob = 100 * len(list(filter(lambda x: x < 1.2, results))) / float(len(results))
		probs.append(prob)
		violations.append(random.choices([0, 1], weights = [prob, 100 - prob], k = 1)[0])
	#print(f"{b1}{' ' * (10 - len(b1))}: {probs[0]} | {b2}{' ' * (10 - len(b2))}: {probs[1]} | {b3}{' ' * (10 - len(b3))}: {probs[2]}")
	return violations

if __name__ == '__main__':
	probabilities(sys.argv[1], sys.argv[2], sys.argv[3])
