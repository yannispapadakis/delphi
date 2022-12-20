#!/usr/bin/python3
from pairing import *
import matplotlib.pyplot as plt
import pandas as pd

def classes_from_file(qos, class_):
	classes = dict()
	for feature in features:
		classes_fd = open(f"{predictions_dir}SVC/SVC_{feature}_{class_}_{qos}_spt_cv.csv")
		classes[feature] = dict((rows[0], int(rows[-1]))
								for rows in filter(lambda x: x[0] != 'Bench' and x[0] != 'Accuracy',
											csv.reader(classes_fd, delimiter='\t')))
		classes_fd.close()
	return classes

def box_plot_classvsclass(qos, class_):
	heatmap = spawn_heatmap()
	read_heatmap(heatmap)
	classes = classes_from_file(qos, class_)
	per_classes = [[{'sd': []} for c in set(classes['cont'].values())] for s in set(classes['sens'].values())]
	
	for bench1 in heatmap:
		for bench2 in heatmap[bench1]:
			per_classes[classes['sens'][bench1]][classes['cont'][bench2]]['sd'].append(heatmap[bench1][bench2])
	dataframes = []
	for s in per_classes:
		for c in s:
			dataframes.append(pd.DataFrame(c).assign(Class = str(per_classes.index(s)) + 'vs' + str(s.index(c))))
	
	df = pd.concat(dataframes)
	df = df.pivot(columns = 'Class', values = 'sd')
	bp = df.boxplot(grid = False, figsize = (20, 10), patch_artist = True,
					rot = (0 if class_ == 2 else 90), return_type = 'both')
	labels = {2: ['Insensitive -\nNon-Contentious', 'Insensitive -\nContentious', \
				  'Sensitive -\nNon-Contentious', 'Sensitive -\nContentious'],
			  3: ['Insensitive -\nNon-Cont.', 'Insensitive -\nMod. Cont.', 'Insensitive -\nContentious',
				  'Mod. Sens. -\nNon-Cont.', 'Mod. Sens. -\nMod. Cont.', 'Mod. Sens. -\nContentious',
				  'Sensitive -\nNon-Cont.', 'Sensitive -\nMod. Cont.', 'Sensitive -\nContentious']}
	color1 = 'dimgray'
	color2 = 'silver'
	lw = 3
	fontsize = 36
	(y_bottom, y_top, y_interval) = (1.0, 3.0, qos - 1.0)

	bp[0].set_xticklabels(labels[class_])
	bp[0].set_yticks(np.arange(y_bottom, y_top, y_interval))

	for whisker in bp[1]['whiskers']: whisker.set(color = color1, linewidth = lw)
	for cap in bp[1]['caps']: cap.set(color = color1, xdata = cap.get_xdata() - (-0.005, +0.005), linewidth = lw)
	for box in bp[1]['boxes']:
		box.set(color = color1, linewidth = lw)
		box.set_facecolor(color2)
	for median in bp[1]['medians']: median.set(color=color1, linewidth = lw)
	for flier in bp[1]['fliers']: flier.set(marker = 'o', markerfacecolor = color2, markeredgecolor = color1, markersize = 6)
	for tick in bp[0].xaxis.get_major_ticks(): tick.label1.set_fontsize(fontsize)
	for tick in bp[0].yaxis.get_major_ticks(): tick.label1.set_fontsize(fontsize - 6)

	plt.ylabel('Slowdown', fontsize = fontsize + 6)
	plt.ylim(bottom = y_bottom, top = y_top)
	plt.axhline(y = qos, color = 'firebrick', linewidth = lw + 1, zorder = 4)
	plt.suptitle('')
	plt.tight_layout()
	plt.savefig(f"{results_dir}ClassVClass_{class_}_{qos}.png")
	plt.clf()

if __name__ == '__main__':
	for qos in qos_levels:
		for c in classes_:
			box_plot_classvsclass(qos, c)
