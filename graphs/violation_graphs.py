#!/usr/bin/python3
import sys
sys.path.append('../pairings/')
from pairing import *
warnings.filterwarnings("ignore", category=RuntimeWarning)
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle, FancyBboxPatch


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
				  'p': ('Pred.', 'Pred.', ''), 'r': ('Real', 'Oracle', ''), 'a': ('Attackers', 'Attackers', ''), '2': ('Conserv.', ''), '3': ('Moderate','')}
		renamed_columns = dict()
		for column in columns:
			tokens = column.split('_')
			new_name =	f"{lookup[tokens[3]][int('delphi' not in tokens[1] or 'a' in tokens[2])]} " + \
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
	(y_bottom, y_top) = (0.0, 30.0)
	if str(slo) == '1.1': plt.ylim(bottom = y_bottom)
	elif str(slo) == '1.2': plt.ylim(bottom = y_bottom, top = y_top - 3.0)
	elif str(slo) == 'all': plt.ylim(bottom = y_bottom, top = y_top)
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
	yhook = -13.50
	if str(slo) == '1.2': yhook += 2.0
	props = dict(boxstyle = 'round', facecolor = 'white', edgecolor = 'black', alpha = 0.5, linewidth = linewidth + 0.5)
	def get_x(df, position): return ((len(set(df.columns)) * position - 3) / 2)
	plt.text(get_x(df, 2), yhook, syst, fontsize = fontsize - 2, ha='center', va = 'center', bbox = props)
	plt.text(get_x(df, 4), yhook, syst, fontsize = fontsize - 2, ha='center', va = 'center', bbox = props)
	plt.text(get_x(df, 6), yhook, syst, fontsize = fontsize - 2, ha='center', va = 'center', bbox = props)
	y_box = 0.2
	dboxl = FancyBboxPatch((get_x(df, 2) - 1.75, y_box), 3.6, 10, boxstyle="round,pad=0.2",fc = 'grey', ec = 'black', zorder = -1, alpha = 0.1)
	yoffset = 2.5
	dboxm = FancyBboxPatch((get_x(df, 4) - 1.75, y_box + yoffset), 3.6, 15.5 - 3 * int('1.2' in str(slo)), boxstyle="round,pad=0.2",fc = 'grey', ec = 'black', zorder = -1, alpha = 0.1)
	yoffset += 2.5 if '1.2' not in str(slo) else 0.0
	dboxh = FancyBboxPatch((get_x(df, 6) - 1.75, y_box + yoffset), 3.6, 15, boxstyle="round,pad=0.2",fc = 'grey', ec = 'black', zorder = -1, alpha = 0.1)
	bp[0].add_patch(dboxl)
	bp[0].add_patch(dboxm)
	bp[0].add_patch(dboxh)

	y1, y2 = plt.ylim()
	xanchor = len(set(df.columns)) - 0.40
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
