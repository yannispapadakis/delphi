#!/usr/bin/python3
from models_backend import *
import matplotlib.pyplot as plt

avg_mode = ['macro', 'weighted'][0]
metrics_str = ['accuracy', 'f1-score', 'precision', 'recall']
title = {'sens': 'Sensitivity', 'cont': 'Contentiousness', 'sp': 'Spec-Parsec', 's': 'Spec', 's-p': 'Train: Spec, Test: Parsec'}

def parse_prediction(args):
	(model, feat, classes, qos, benches, run) = args
	fd = open(predictions_dir  + model + '/' + '_'.join([model, feat, str(classes), str(qos), benches, run]) + '.csv', 'r')
	predictions = dict((row[0], (int(row[1]), int(row[2]))) for row in list(filter(lambda x: "Bench" not in x[0], csv.reader(fd, delimiter = "\t"))))
	y_pred = list(map(lambda x: x[0], predictions.values()))
	y_true = list(map(lambda x: x[1], predictions.values()))
	metrics_ = metrics.classification_report(y_true, y_pred, digits=4, zero_division = 0, output_dict = True)
	return {'accuracy': metrics_['accuracy'], 'f1-score': metrics_[avg_mode + ' avg']['f1-score'],
			'precision': metrics_[avg_mode + ' avg']['precision'], 'recall': metrics_[avg_mode + ' avg']['recall']}

def get_metrics(feat, c, qos, benches, run, metric):
	fd = open(graphs_dir + '_'.join([benches, run]) + '/' + 'metrics_report.txt', 'a')
	d = dict((model, parse_prediction([model, feat,c, qos, benches, run])) for model in models)
	(max_model, max_met) = max(d.items(), key = lambda x: x[1][metric])
	prefix = f"{title[feat]}{' ' * (15 - len(title[feat]))} {c} {qos} | Highest"
	msg = f"{prefix if metric == metrics_str[0] else ' ' * len(prefix)}{' ' * (10 - len(metric))}{metric}:  {max_model}{' ' * (6 - len(max_model))}{100 * max_met[metric]:.2f}% | "
	msg += ' | '.join([f"{m[0].upper()}: {100 * max_met[m]:.2f}%" for m in max_met])
	fd.write(f"{msg}\n")
	if metric == metrics_str[-1]: fd.write(f"{'-' * len(msg)}\n")
	fd.close()
	return {'model': list(d.keys()), metric: [d[model][metric] for model in d]}

def bar_graphs(feat, c, qos, benches, run, metric):
	df = pd.DataFrame.from_dict(get_metrics(feat, c, qos, benches, run, metric))
	df = df.set_index('model')

	ax = df.plot.bar(figsize = (35,20), ylim=(0.0, 1.0), rot = 0, zorder=3, legend=False)
	ax.grid(axis='y', zorder = 0)
	ax.set_title(', '.join([title[feat], str(c), str(qos), title[benches], run.upper()]), fontsize = 40)
	for bar in ax.patches: bar.set_edgecolor('black')
	for tick in ax.xaxis.get_major_ticks(): tick.label.set_fontsize(35)
	for tick in ax.yaxis.get_major_ticks(): tick.label.set_fontsize(35)

	plt.xlabel("Model", fontsize = 35)
	plt.ylabel(metric.capitalize(), fontsize = 35)
	plt.tight_layout()
	plt.savefig(graphs_dir + '_'.join([benches, run]) + '/' +  '_'.join([benches, run, str(c), str(qos), feat, metric]) + '.png')
	plt.close()

def accuracy_metrics(args):
	arg_check(args)
	(benches, run) = args[1:]
	for (feat, c, qos, metric) in list(product(*[features, classes_, qos_levels, metrics_str])):
		bar_graphs(feat, c, qos, benches, run, metric)

def find_benches_runs():
	bench_runs = []
	for model in os.listdir(predictions_dir):
		for pred in os.listdir(predictions_dir + model):
			bench_runs.append('_'.join(pred.split('.csv')[0].split('_')[4:6]))
	return list(set(bench_runs))

def arg_check(args):
	bench_runs = find_benches_runs()
	if len(args) != 3 or '_'.join(args[1:]) not in bench_runs:
		print(f"Usage:\t\t{args[0]} <benches> <run> <metric>")
		print(f"Benches, Runs:\t{' | '.join(map(lambda x: x.replace('_',' '), bench_runs))}")
		sys.exit(1)

if __name__ == "__main__":
	accuracy_metrics(sys.argv)
