#!/usr/bin/python3
from models_backend import *

avg_mode = ['macro', 'weighted'][1]

def parse_prediction(args):
	(model, feat, classes, qos, benches, run) = args
	fd = open(predictions_dir  + model + '/' + '_'.join([model, feat, str(classes), str(qos), benches, run]) + '.csv', 'r')
	predictions = dict((row[0], (int(row[1]), int(row[2]))) for row in list(filter(lambda x: "Bench" not in x[0], csv.reader(fd, delimiter = "\t"))))
	y_pred = list(map(lambda x: x[0], predictions.values()))
	y_true = list(map(lambda x: x[1], predictions.values()))
	#print(metrics.confusion_matrix(y_true, y_pred))
	metrics_ = metrics.classification_report(y_true, y_pred, digits=4, zero_division = 0, output_dict = True)
	return (metrics_['accuracy'], metrics_[avg_mode + ' avg']['f1-score'])

def metrics_per_model(feat, c, qos, benches, run):
	acc_metrics = dict((model, parse_prediction([model, feat, c, qos, benches, run])) for model in models)
#	for model in acc_metrics: print(f"\t{model}\t{acc_metrics[model][0]:.3f}\t{acc_metrics[model][1]:.3f}")
	acc_max = max(acc_metrics.items(), key = lambda x: x[1][0])
	f1_max = max(acc_metrics.items(), key = lambda x: x[1][1])
	print(f"{feat} {c} {qos}")
	print(f"Model with highest accuracy: {acc_max[0]}  \tAccuracy: {acc_max[1][0]:.3f}\tf1-score: {acc_max[1][1]:.3f}")
	print(f"Model with highest f1 score: {f1_max[0]}  \tAccuracy: {f1_max[1][0]:.3f}\tf1-score: {f1_max[1][1]:.3f}")

def accuracy_metrics(benches, run):
	for feat in features:
		for c in classes_:
			for qos in qos_levels:
				metrics_per_model(feat, c, qos, benches, run)

if __name__ == "__main__":
	accuracy_metrics('s-p', 'test')
