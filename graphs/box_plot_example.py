#!/usr/bin/python3
from violation_graphs import *

def box_plot_example():
	(app1, app2, app3) = ('sjeng-2', 'img-dnn-2', 'perlbench-1')
	with open(f"{heatmap_dir}heatmap.csv") as h_fd:
		heatmap = pd.read_csv(h_fd, delimiter = '\t')
	heatmap = heatmap.rename(columns={'Unnamed: 0': 'Bench'})
	to_plot = heatmap.loc[(heatmap['Bench'] == app1) | (heatmap['Bench'] == app2) | (heatmap['Bench'] == app3)]
	to_plot = to_plot.replace(app1, 'Application 1').replace(app2, 'Application 3').replace(app3, 'Application 2')
	to_plot = to_plot.set_index('Bench')
	to_plot = to_plot.transpose()

	bp = to_plot.boxplot(column = ['Application 1', 'Application 2', 'Application 3'],
						 grid = False, figsize = (20, 10), patch_artist = True,
						 return_type = 'both')
	lw = 3
	color1 = 'dimgray'
	color2 = 'silver'
	fontsize = 36

	for whisker in bp[1]['whiskers']: whisker.set(color = color1, linewidth = lw)
	for cap in bp[1]['caps']: cap.set(color=color1, xdata=cap.get_xdata() - (-0.005,+0.005), linewidth = lw)
	for box in bp[1]['boxes']:
		box.set(color=color1, linewidth = lw)
		box.set_facecolor(color2)
	for median in bp[1]['medians']: median.set(color=color1, linewidth = lw)
	for (i,flier) in enumerate(bp[1]['fliers']):
		flier.set(marker = 'o',
				  markerfacecolor = color1 if i < 2 else 'white',
				  markeredgecolor = color1 if i < 2 else 'white',
				  markersize = 6)
	plt.ylabel('Slowdown', fontsize = fontsize + 6)
	plt.ylim(top=2.1)
	plt.yticks([])
	for tick in bp[0].xaxis.get_major_ticks(): tick.label1.set_fontsize(fontsize)

	arrowprops1 = dict(arrowstyle = "->",
					connectionstyle = "angle, angleA = 300, angleB = 60,rad = 100", linewidth = lw - 1)
	arrowprops2 = dict(arrowstyle = "->",
					connectionstyle = "angle, angleA = 270, angleB = 340, rad = 120", linewidth = lw - 1)
	arrowprops3 = dict(arrowstyle = "->",linewidth = lw - 1,
					connectionstyle = "angle, angleA = 260, angleB = 100,rad = 120")

	plt.annotate('Conservative Cl.: Insensitive\nModerate Cl.: Insensitive', xy = (1.06, 1.06), xytext = (1.125, 1.4), fontsize = fontsize, arrowprops = arrowprops1, ha='center')
	plt.annotate('Conservative Cl.: Sensitive\nModerate Cl.: Moderately Sensitive', xy = (2.06, 1.235), xytext = (2, 1.6), fontsize = fontsize, arrowprops = arrowprops1, ha='center')
	xt2 = 2.9
	plt.annotate('Conservative Cl.: Sensitive', xy = (2.94, 1.8), xytext = (xt2, 1.95), fontsize = 36, ha='center')
	plt.annotate('', xy = (3.09, 1.82), xytext = (3.45, 1.94), arrowprops = arrowprops2)
	plt.annotate('Moderate Cl.: Sensitive', xy = (3.15, 1.35), xytext = (xt2, 1.93), fontsize = 36, ha='center',va='top')
	plt.annotate('', xy = (2.87, 1.35), xytext = (2.87, 1.87), arrowprops = arrowprops3, ha='right',va='top')
	plt.axhline(y = 1.2, color = "firebrick", linewidth = lw, zorder = 4)
	plt.suptitle('')
	plt.tight_layout()
	plt.savefig(f'{results_dir}BoxPlotExample.png')
	plt.close()

if __name__ == '__main__':
	box_plot_example()
