#!/usr/bin/python3
from violation_graphs import *

def pareto_plot():
	def is_pareto_efficient(costs):
		is_efficient = np.ones(costs.shape[0], dtype = bool)
		for i, c in enumerate(costs):
			is_efficient[i] = np.all(np.any(costs[:i]>c, axis=1)) and np.all(np.any(costs[i+1:]>c, axis=1))
		return is_efficient

	with open(f"{violations_dir}boxplot-1.2.csv", 'r') as violations_file:
		df = pd.read_csv(violations_file, delimiter = ',')
	df.set_index('algo', inplace=True)
	bv = df[['bins', 'violations']].values
	efficient_points = bv[is_pareto_efficient(bv)]

	fig, ax = plt.subplots()
	x = df['bins'].values
	y = df['violations'].values
	algo = df.index.values

	markers = {'random': {'2': {'c': 'X'}}, 
			   'oracle': {'2': {'c': 'o'}}, 
			   'delphi': {'2': {'c':'^', 'r': 'v'}, '3': {'c':'>', 'r': '<'}}, 
			   'attackers': {'2': {'c': 's', 'r': 'D'}}}
	colors = {'r': 'black', 'p': 'red'}

	for i in range(len(x)):
		(alg, pred, cl, mode) = algo[i].split('_')
		ax.scatter(x[i], y[i], marker=markers[alg][cl][mode], color=colors[pred], label = algo[i])
	ax.plot(sorted(efficient_points[:, 0], reverse = True), sorted(efficient_points[:, 1]), color='red', label='Pareto Frontier')
	ax.legend()

	plt.xlabel('Bins')
	plt.ylabel('Violations')
	plt.title('Pareto Frontier')
	plt.legend(bbox_to_anchor=(1, 1))
	plt.savefig(f"{violations_dir}/pareto.png")

if __name__=='__main__':
	pareto_plot()
