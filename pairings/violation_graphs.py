#!/usr/bin/python3
from pairing import *
warnings.filterwarnings("ignore", category=RuntimeWarning)
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle, FancyBboxPatch

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

def all_violations_boxplots(args):
	try:
		args[1] == 'new'
		run_all_algorithms(args[1:])
	except: pass
	finally:
		for slo in map(lambda x: x.split('-')[1].split('.csv')[0], filter(lambda x: 'boxplot' in x, os.listdir(f"{violations_dir}"))):
			violations_boxplot(slo)

def violations_boxplot(slo):
	def column_rename(columns):
		lookup = {'random': 'Random', 'oracle': 'Heatmap', 'whisker': 'Whisker', 'delphi': '', 'delphi3': 'N', \
				  'p': ('Pred.', 'Pred.', ''), 'r': ('Real', 'Oracle', ''), '2': ('Conserv.', ''), '3': ('Moderate','')}
		renamed_columns = dict()
		for column in columns:
			tokens = column.split('_')
			new_name =	f"{lookup[tokens[3]][int('delphi' not in tokens[1])]} " + \
						f"{lookup[tokens[2]][int('delphi' not in tokens[1]) + int(tokens[1] == 'random' or tokens[1] == 'whisker')]} " + \
						f"{lookup[tokens[1]]}"
			renamed_columns[column] = new_name.strip()
		return renamed_columns

	with open(f"{violations_dir}boxplot-{slo}.csv", 'r') as violations_file:
		df = pd.read_csv(violations_file, delimiter = ',')
	df = df.rename(columns = column_rename(df.columns))
	bp = df.boxplot(figsize = (21,15), return_type = 'both', rot = 90, patch_artist=True)

	edgecs = ['#227522'] * len(set(df.columns)) + ['#757522'] * len(set(df.columns)) + ['#752222'] * len(set(df.columns))
	colors = ['#A5DCA5'] * len(set(df.columns)) + ['#DCDCA5'] * len(set(df.columns)) + ['#DCA5A5'] * len(set(df.columns))
	linewidth = 2
	fontsize = 32
	#bp[0].set_xticklabels(labels)
	#plt.yticks(np.arange(0.0, 22.6 if sla < 1.3 else 27.6, 2.5))
	for (patch, color, edgec) in zip(bp[1]['boxes'], colors, edgecs):
		patch.set(color = edgec, linewidth = linewidth)
		patch.set_facecolor(color)
	for (i, whisker) in enumerate(bp[1]['whiskers']): whisker.set(color = edgecs[i // 2], linewidth = linewidth)
	for (i, cap) in enumerate(bp[1]['caps']):
		cap.set(color=edgecs[i // 2], xdata=cap.get_xdata() - (-0.005,+0.005), linewidth = linewidth)
	for (median, color) in zip(bp[1]['medians'], edgecs): median.set(color=color, linewidth = linewidth)
	for (flier, color, edgec) in zip(bp[1]['fliers'], colors, edgecs):
		flier.set(marker = 'o', markerfacecolor = color, markeredgecolor = edgec, markersize = 8)
	for tick in bp[0].xaxis.get_major_ticks(): tick.label1.set_fontsize(fontsize)
	for tick in bp[0].yaxis.get_major_ticks(): tick.label1.set_fontsize(fontsize)
	plt.ylabel('Violations', fontsize = fontsize + 10)

	syst = '     Delphi     '
	yhook = -14.50
	props = dict(boxstyle = 'round', facecolor = 'white', edgecolor = 'black', alpha = 0.5, linewidth = linewidth + 0.5)
	plt.text(((len(set(df.columns)) * 2 - 3) / 2), yhook, syst, fontsize = fontsize - 2, ha='center', va = 'center', bbox = props)
	plt.text(((len(set(df.columns)) * 4 - 3) / 2), yhook, syst, fontsize = fontsize - 2, ha='center', va = 'center', bbox = props)
	plt.text(((len(set(df.columns)) * 6 - 3) / 2), yhook, syst, fontsize = fontsize - 2, ha='center', va = 'center', bbox = props)

	y1, y2 = plt.ylim()
	xanchor = len(set(df.columns))
	yanchor = y2 - 1.6
	box_size = 0.5
	interval = 0.1
	rbox = FancyBboxPatch((xanchor, yanchor - 0.1), 9, 1.25, boxstyle="round,pad=0.2",fc = 'white', ec = 'black', zorder = 3)
	plt.text(xanchor, yanchor + 0.1, 'Intensity:', fontsize = fontsize - 2)
	bp[0].add_patch(rbox)
	xanchor += 2.6
	bp[0].add_patch(Rectangle((xanchor,yanchor), box_size, 1, facecolor = colors[0], zorder = 4))
	plt.text(xanchor + box_size + interval, yanchor + 0.1, 'Low', fontsize = fontsize - 2)
	xanchor += box_size + 1.25
	bp[0].add_patch(Rectangle((xanchor, yanchor), box_size, 1, facecolor = colors[len(set(df.columns))], zorder = 4))
	plt.text(xanchor + box_size + interval, yanchor + 0.1, 'Medium', fontsize = fontsize - 2)
	xanchor += box_size + 2.3
	bp[0].add_patch(Rectangle((xanchor, yanchor), box_size, 1, facecolor = colors[2 * len(set(df.columns))], zorder = 4))
	plt.text(xanchor + box_size + interval, yanchor + 0.1, 'High', fontsize = fontsize - 2)

	plt.tight_layout()
	previous_runs = len(list(filter(lambda x: f"violations_{slo}" in x, os.listdir(f"{violations_dir}"))))
	plt.savefig(f"{violations_dir}/violations_{slo}_{previous_runs}.png")
	plt.clf()

if __name__ == '__main__':
	try: mode = sys.argv[1]
	except: mode = ''
	if mode == 'new' or not mode:
		all_violations_boxplots(sys.argv)
	elif mode == 'cvc':
		for qos in qos_levels:
			for c in classes_:
				box_plot_classvsclass(qos, c)
