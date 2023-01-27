#!/usr/bin/python3
import sys
sys.path.append('../predict/')
from models_backend import *
import matplotlib.pyplot as plt

avg_mode = ['macro', 'weighted'][0]
metrics_str = ['accuracy', 'f1-score', 'precision', 'recall']
models_included = [models, chosen_models][1]

def parse_prediction(args):
	(model, feat, classes, qos, benches, run) = args
	try: fd = open(predictions_dir  + model + '/' + '_'.join([model, feat, str(classes), str(qos), benches, run]) + '.csv', 'r')
	except: return dict()
	predictions = dict((row[0], (int(row[1]), int(row[2]))) for row in list(filter(lambda x: "Bench" not in x[0] and "Accuracy" not in x[0], csv.reader(fd, delimiter = "\t"))))
	y_pred = list(map(lambda x: x[0], predictions.values()))
	y_true = list(map(lambda x: x[1], predictions.values()))
	metrics_ = metrics.classification_report(y_true, y_pred, digits=4, zero_division = 0, output_dict = True)
	with open(f"{gridsearch_dir}{feat}_{classes}_{qos}_{benches}.txt", 'r') as acc_fd:
		acc_d = {x[0]: float(x[-2]) for x in csv.reader(acc_fd, delimiter = '\t')}
	return {'accuracy': metrics_['accuracy'], 'f1-score': metrics_[avg_mode + ' avg']['f1-score'],
			'precision': metrics_[avg_mode + ' avg']['precision'], 'recall': metrics_[avg_mode + ' avg']['recall']}
	#return {'accuracy': acc_d[model], 'f1-score': metrics_[avg_mode + ' avg']['f1-score'],

def get_metrics(feat, benches, run, metric):
	def string(c): return f"{c[1]}{'C' if c[0] == 2 else 'M'}"
	os.makedirs(f"{graphs_dir}{'_'.join([benches, run])}", exist_ok = True)
	d = {'SLO': map(string, list(product(*[classes_, qos_levels])))}
	for model in models_included:
		d[model] = [parse_prediction([model, feat, c, qos, benches, run])[metric] for (c, qos) in list(product(*[classes_, qos_levels]))]
	return d

def bar_graphs(feat, benches, run, metric):
	df = pd.DataFrame.from_dict(get_metrics(feat, benches, run, metric))
	df = df.set_index('SLO')

	colors  = ['rosybrown', 'silver', 'steelblue', 'goldenrod']
	hatches = len(df) * ['-'] + len(df) * ['/'] + len(df) * [''] + len(df) * ['\\']
	labels = list(map(str, qos_levels)) * 2
	fontsize = 35

	ax = df.plot.bar(color = colors, figsize = (15,10), ylim=(0.5, 1.0), rot = 0, zorder = 3, legend = False)
	ax.grid(axis='y', zorder = 0)
	ax.set_xticklabels(labels)
	for bar, hatch in zip(ax.patches, hatches):
		bar.set_hatch(hatch)
		bar.set_edgecolor('black')
	for tick in ax.xaxis.get_major_ticks(): tick.label.set_fontsize(fontsize)
	for tick in ax.yaxis.get_major_ticks(): tick.label.set_fontsize(fontsize)

	ax.legend(bbox_to_anchor = (0, 1, 1, 0), loc='lower center', frameon=False, fontsize = fontsize - 5, ncol = 4)
	class_definitions = ['Conservative Classification', 'Moderate Classification']
	ax.yaxis.set_label_coords(-0.11, 0.5)
	ax.xaxis.set_label_coords(0.5, -0.2)
	for (i, cd) in enumerate(class_definitions): plt.text(3 * i + 1, 0.425, cd, fontsize = fontsize, ha='center')
	plt.xlabel("SLO", fontsize = fontsize)
	plt.ylabel(metric.capitalize(), fontsize = fontsize)
	plt.tight_layout()
	plt.savefig(f"{graphs_dir}{benches}_{run}/{feat}_{metric}.png")
	plt.close()

def accuracy_metrics(args):
	bench_runs = set(['_'.join(pred.split('.csv')[0].split('_')[4:6]) for model in os.listdir(predictions_dir) for pred in os.listdir(predictions_dir + model)])
	if len(args) != 3 or '_'.join(args[1:]) not in bench_runs:
		print(f"Usage:\t{args[0]} <benches> <run>:\t{' | '.join(map(lambda x: x.replace('_',' '), bench_runs))}")
	else:
		(benches, run) = args[1:]
		for (feat, metric) in list(product(*[features, metrics_str])): bar_graphs(feat, benches, run, metric)

if __name__ == "__main__":
	accuracy_metrics(sys.argv)
