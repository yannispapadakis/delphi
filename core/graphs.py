import os, sys, csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from grid import *
from matplotlib.patches import Rectangle, FancyBboxPatch

res_dir = '/home/ypap/characterization/results/'

def box_plot_example():
	g_fd = open(res_dir + 'grids/grid.csv')
	grid = pd.read_csv(g_fd, delimiter = '\t')
	grid = grid.rename(columns={'Unnamed: 0': 'Bench'})
	to_plot = grid.loc[(grid['Bench'] == 'sjeng-2') | (grid['Bench'] == 'mcf-1') | (grid['Bench'] == 'perlbench-1')]
	to_plot = to_plot.replace('mcf-1', 'Application 3').replace('sjeng-2', 'Application 1').replace('perlbench-1', 'Application 2')
	to_plot = to_plot.set_index('Bench')
	plotT = to_plot.transpose()

	bp = plotT.boxplot(column=['Application 1', 'Application 2', 'Application 3'],
						grid = False, figsize = (20, 10),patch_artist=True,
						return_type = 'both')

	lw = 3

	colour1 = 'dimgray'
	colour2 = 'silver'
	for whisker in bp[1]['whiskers']:
		whisker.set(color = colour1,
					linewidth = lw)
	for cap in bp[1]['caps']:
		cap.set(color=colour1,
				xdata=cap.get_xdata() - (-0.005,+0.005),
				linewidth = lw)
	for box in bp[1]['boxes']:
		box.set(color=colour1, linewidth = lw)
		box.set_facecolor(colour2)
	for median in bp[1]['medians']:
		median.set(color=colour1,
					linewidth = lw)
	for (i,flier) in enumerate(bp[1]['fliers']):
		flier.set(	marker = 'o',
					markerfacecolor = colour1 if i < 2 else 'white',
					markeredgecolor = colour1 if i < 2 else 'white',
					markersize = 6)

	for tick in bp[0].xaxis.get_major_ticks():
		tick.label.set_fontsize(36)
	for tick in bp[0].yaxis.get_major_ticks():
		tick.label.set_fontsize(36)

	plt.ylabel('Slowdown', fontsize = 42)
	plt.ylim(top=2.0)

	arrowprops = dict(arrowstyle = "->",
					connectionstyle = "angle, angleA = 300, angleB = 60,rad = 100", linewidth = lw - 1)
	arrowprops2 = dict(arrowstyle = "->",
					connectionstyle = "angle, angleA = 270, angleB = 340, rad = 120", linewidth = lw - 1)
	arrowprops3 = dict(arrowstyle = "->",linewidth = lw - 1,
					connectionstyle = "angle, angleA = 260, angleB = 100,rad = 120")

	plt.annotate('Conservative Cl.: Insensitive\nModerate Cl.: Insensitive', xy = (1.06, 1.06), xytext = (1.125, 1.4), fontsize = 36, arrowprops = arrowprops, ha='center')
	plt.annotate('Conservative Cl.: Sensitive\nModerate Cl.: Moderately Sensitive', xy = (2.06, 1.235), xytext = (2, 1.6), fontsize = 36, arrowprops = arrowprops, ha='center')
	xt2 = 2.9
	plt.annotate('Conservative Cl.: Sensitive', xy = (2.94, 1.8), xytext = (xt2, 1.9), fontsize = 36, ha='center')
	plt.annotate('', xy = (3.09, 1.8), xytext = (3.45, 1.89), arrowprops = arrowprops2)
	plt.annotate('Moderate Cl.: Sensitive', xy = (3.15, 1.35), xytext = (xt2, 1.88), fontsize = 36, ha='center',va='top')
	plt.annotate('', xy = (2.87, 1.35), xytext = (2.87, 1.82), arrowprops = arrowprops3, ha='right',va='top')
	plt.axhline(y = 1.2, color = "firebrick", linewidth = lw, zorder = 4)
	plt.suptitle('')
	plt.tight_layout()
	plt.savefig('./BoxPlotExample.png')

def box_plot_class(feat, cc):
	grid = generate_grid()
	read_grid(grid)
	classes_fd = open(res_dir + 'predictions/SVC/' + feat + '_' + str(cc) + '_1.2_SVC.csv', 'r')
	reader = csv.reader(classes_fd, delimiter = '\t')
	classes = dict((rows[0], int(rows[-1])) for rows in 
					[x for x in reader if x[0] != 'Bench' and x[0] != 'Accuracy'])
	per_classes = []
	for cl in set(classes.values()):
		per_class = {'sd': []}
		per_classes.append(per_class)
	for bench in grid:
		per_classes[classes[bench]]['sd'].extend(grid[bench].values())
	dfs = []
	for d in per_classes:
		dfs.append(pd.DataFrame(d).assign(Class = per_classes.index(d)))

	df = pd.concat(dfs)
	df = df.pivot(columns='Class', values='sd')
	lw = 4
	bp = df.boxplot(column=list(set(classes.values())),
					grid = False, figsize = (20, 10),
					return_type = 'both')

	colour1 = 'DarkBlue'
	for whisker in bp[1]['whiskers']:
		whisker.set(color = colour1,
					linewidth = lw)
	for cap in bp[1]['caps']:
		cap.set(color=colour1,
				xdata=cap.get_xdata() - (-0.005,+0.005),
				linewidth = lw)
	for box in bp[1]['boxes']:
		box.set(color=colour1, linewidth = lw)
	for median in bp[1]['medians']:
		median.set(color=colour1,
					linewidth = lw)
	for flier in bp[1]['fliers']:
		flier.set(	marker = 'o',
					markerfacecolor = colour1,
					markeredgecolor = colour1,
					markersize = 6)

	for tick in bp[0].xaxis.get_major_ticks():
		tick.label.set_fontsize(36)
	for tick in bp[0].yaxis.get_major_ticks():
		tick.label.set_fontsize(36)

	plt.ylabel('Slowdown', fontsize = 42)
	plt.ylim(top=2.0)
	plt.axhline(y = 1.2, color = "firebrick", linewidth = lw)
	plt.suptitle('')
	plt.savefig('./' + feat + str(cc) + '.png')

def violation_bp(sla):
	viols_f = open(res_dir + 'violations/boxplots/' + 'bp-' + str(sla) + '.csv')
	df = pd.read_csv(viols_f, delimiter = '\t')
	labels = ['Random', 'Heatmap (Oracle)', 'Attackers', 'Predicted Heatmap', 'Conserv. Real', 'Conserv. Pred.', 'Moderate Real', 'Moderate Pred.'] * 3
	lw = 2
	bp = df.boxplot(column=list(df.columns), figsize = (21,15), return_type = 'both', rot = 90, patch_artist=True)
	bp[0].set_xticklabels(labels)
	plt.yticks(np.arange(0.0, 22.6 if sla < 1.3 else 27.6, 2.5))

	edgecs = ['#227522'] * 8 + ['#757522'] * 8 + ['#752222'] * 8
	colors = ['#A5DCA5'] * 8 + ['#DCDCA5'] * 8 + ['#DCA5A5'] * 8
	for (patch, color, edgec) in zip(bp[1]['boxes'], colors, edgecs):
		patch.set(color = edgec, linewidth = lw)
		patch.set_facecolor(color)
#		patch.set_hatch('.')
	for (i, whisker) in enumerate(bp[1]['whiskers']):
		whisker.set(color = edgecs[i // 2],
					linewidth = lw)
	for (i, cap) in enumerate(bp[1]['caps']):
		cap.set(color=edgecs[i // 2],
				xdata=cap.get_xdata() - (-0.005,+0.005),
				linewidth = lw)
	for (median, color) in zip(bp[1]['medians'], edgecs):
		median.set(color=color,
					linewidth = lw)
	for (flier, color, edgec) in zip(bp[1]['fliers'], colors, edgecs):
		flier.set(	marker = 'o',
					markerfacecolor = color,
					markeredgecolor = edgec,
					markersize = 8)
	for tick in bp[0].xaxis.get_major_ticks():
		tick.label.set_fontsize(32)
	for tick in bp[0].yaxis.get_major_ticks():
		tick.label.set_fontsize(32)

	plt.ylabel('Violations', fontsize = 42)

#	cd1 = 'Conservative\nClassification'
#	cd2 = 'Moderate\nClassification'
#
#	cd1 = cd2 = ''
#	yhook = -4.2
#	rr = 90
#	if sla == 1.3: yhook -= 1
#	plt.text((11 / 2), yhook, cd1, fontsize = 30, ha='center', va = 'top', rotation = rr)
#	plt.text((15 / 2), yhook, cd2, fontsize = 30, ha='center', va = 'top', rotation = rr)
#	plt.text((27 / 2), yhook, cd1, fontsize = 30, ha='center', va = 'top', rotation = rr)
#	plt.text((31 / 2), yhook, cd2, fontsize = 30, ha='center', va = 'top', rotation = rr)
#	plt.text((43 / 2), yhook, cd1, fontsize = 30, ha='center', va = 'top', rotation = rr)
#	plt.text((47 / 2), yhook, cd2, fontsize = 30, ha='center', va = 'top', rotation = rr)
	syst = '        ' + 'Delphi' + '        '
	syst = '   Delphi   '
	yhook = -11.25
	if sla == 1.3: yhook -= 2.25
	llw = 2.5
	props = dict(boxstyle='round', facecolor='white', edgecolor = 'black', alpha=0.5, linewidth = llw)
	plt.text((13 / 2), yhook, syst, fontsize = 30, ha='center', va = 'center', bbox = props)
	plt.text((29 / 2), yhook, syst, fontsize = 30, ha='center', va = 'center', bbox = props)
	plt.text((45 / 2), yhook, syst, fontsize = 30, ha='center', va = 'center', bbox = props)

	y1, y2 = plt.ylim()
	xanchor = 8
	yanchor = y2 - 1.6
	box_size = 0.5
	interval = 0.1
	rbox = FancyBboxPatch((xanchor, yanchor - 0.1), 9, 1.25, boxstyle="round,pad=0.2",fc = 'white', ec = 'black', zorder = 3)
	plt.text(xanchor, yanchor + 0.1, 'Intensity:', fontsize = 30)
	bp[0].add_patch(rbox)
	xanchor += 2.6
	bp[0].add_patch(Rectangle((xanchor,yanchor), box_size, 1, facecolor = colors[0], zorder = 4))
	plt.text(xanchor + box_size + interval, yanchor + 0.1, 'Low', fontsize = 30)
	xanchor += box_size + 1.25
	bp[0].add_patch(Rectangle((xanchor, yanchor), box_size, 1, facecolor = colors[8], zorder = 4))
	plt.text(xanchor + box_size + interval, yanchor + 0.1, 'Medium', fontsize = 30)
	xanchor += box_size + 2.3
	bp[0].add_patch(Rectangle((xanchor, yanchor), box_size, 1, facecolor = colors[16], zorder = 4))
	plt.text(xanchor + box_size + interval, yanchor + 0.1, 'High', fontsize = 30)

	plt.tight_layout()
	plt.savefig('./violations_' + str(sla) + '.png')

def bp_cvc(cc):
	grid = generate_grid()
	read_grid(grid)
	sens_fd = open(res_dir + 'predictions/SVC/sens_' + str(cc) + '_1.2_SVC.csv', 'r')
	reader = csv.reader(sens_fd, delimiter = '\t')
	sens = dict((rows[0], int(rows[-1])) for rows in 
				[x for x in reader if x[0] != 'Bench' and x[0] != 'Accuracy'])
	cont_fd = open(res_dir + 'predictions/SVC/cont_' + str(cc) + '_1.2_SVC.csv', 'r')
	reader = csv.reader(cont_fd, delimiter = '\t')
	cont = dict((rows[0], int(rows[-1])) for rows in
				[x for x in reader if x[0] != 'Bench' and x[0] != 'Accuracy'])
	per_classes = []
	for s in set(sens.values()):
		sclass = []
		for c in set(cont.values()):
			per_class = {'sd': []}
			sclass.append(per_class)
		per_classes.append(sclass)

	for bench1 in grid:
		bench1_class = sens[bench1]
		for bench2 in grid[bench1]:
			bench2_class = cont[bench2]
			per_classes[bench1_class][bench2_class]['sd'].append(grid[bench1][bench2])

	dfs = []
	for s in per_classes:
		for c in s:
			dfs.append(pd.DataFrame(c).assign(Class = str(per_classes.index(s)) + 'vs' + str(s.index(c))))

	lw = 3
	df = pd.concat(dfs)
	df = df.pivot(columns='Class', values='sd')
	bp = df.boxplot(grid = False, figsize = (20, 10),patch_artist=True,rot=(0 if cc == 2 else 90),
					return_type = 'both')

	labels = {2: ['Insensitive -\nNon-Contentious', 'Insensitive -\nContentious', 'Sensitive -\nNon-Contentious', 'Sensitive -\nContentious'],
			  3: ['Insensitive -\nNon-Cont.', 'Insensitive -\nMod. Cont.', 'Insensitive -\nContentious',
				  'Mod. Sens. -\nNon-Cont.', 'Mod. Sens. -\nMod. Cont.', 'Mod. Sens. -\nContentious',
				  'Sensitive -\nNon-Cont.', 'Sensitive -\nMod. Cont.', 'Sensitive -\nContentious']}
	bp[0].set_xticklabels(labels[cc])
	colour1 = 'dimgray'
	colour2 = 'silver'
	for whisker in bp[1]['whiskers']:
		whisker.set(color = colour1,
					linewidth = lw)
	for cap in bp[1]['caps']:
		cap.set(color=colour1,
				xdata=cap.get_xdata() - (-0.005,+0.005),
				linewidth = lw)
	for box in bp[1]['boxes']:
		box.set(color=colour1, linewidth = lw)
		box.set_facecolor(colour2)
	for median in bp[1]['medians']:
		median.set(color=colour1,
					linewidth = lw)
	for flier in bp[1]['fliers']:
		flier.set(	marker = 'o',
					markerfacecolor = colour2,
					markeredgecolor = colour1,
					markersize = 6)

	for tick in bp[0].xaxis.get_major_ticks():
		tick.label.set_fontsize(36)
	for tick in bp[0].yaxis.get_major_ticks():
		tick.label.set_fontsize(36)

	plt.ylabel('Slowdown', fontsize = 42)
	#plt.ylim(top=2.0)
	plt.axhline(y = 1.2, color = "firebrick", linewidth = lw + 1, zorder = 4)
	plt.suptitle('')
	plt.tight_layout()
	plt.savefig('./ClassVClass' + str(cc) + '.png')

def bar_plot_adapt(feat, cl):
#	adapt_f = open(res_dir + 'adaptivity/' + feat + '_' + str(cl) + '.csv')
	f1 = True
	adapt_f = open(res_dir + 'adaptivity/' + ('f1/' if f1 else '') + feat + '.csv')
	df = pd.read_csv(adapt_f)
	df = df.set_index('SLA')
	cd1 = 'Conservative Classification'
	cd2 = 'Moderate Classification'
	titles = {('sens', 2): cd1 + '\nSensitivity', ('cont', 2): cd1 + '\nContentiousness', ('sens', 3): cd2 + '\nSensitivity', ('cont', 3): cd2 + '\nContentiousness'}
	titles = {'sens': 'Sensitivity', 'cont': 'Contentiousness'}

	colors  = ['rosybrown', 'silver', 'steelblue', 'goldenrod']
	hatches = len(df) * ['-'] + len(df) * ['/'] + len(df) * [''] + len(df) * ['\\']
	ax = df.plot.bar(color = colors, figsize = (15,10), ylim=(0.5, 1.0), rot = 0, zorder=3)
	ax.grid(axis='y', zorder = 0)
	labels = ['1.1', '1.2', '1.3'] * 2
	ax.set_xticklabels(labels)
	bars = ax.patches
	for bar, hatch in zip(bars, hatches):
		bar.set_hatch(hatch)
		bar.set_edgecolor('black')
#	ax.set_title(titles[feat], fontsize = 40)
	for tick in ax.xaxis.get_major_ticks():
		tick.label.set_fontsize(35)
	for tick in ax.yaxis.get_major_ticks():
		tick.label.set_fontsize(35)
	plt.xlabel("SLO", fontsize = 35)
	plt.ylabel('F1 Score' if f1 else 'Accuracy', fontsize = 35)
	ax.yaxis.set_label_coords(-0.11, 0.5)
	ax.xaxis.set_label_coords(0.5, -0.2)
	ax.legend(loc='upper center', frameon=False, fontsize = 30, ncol = 4)
	plt.text(1, 0.425, cd1, fontsize = 35, ha='center')
	plt.text(4, 0.425, cd2, fontsize = 35, ha='center')
	plt.tight_layout()
	plt.savefig(('./f1_' if f1 else './acc_')  + feat + '.png')

def multsla(feat):
	f1 = True
	adapt_f = open(res_dir + 'adaptivity/' + ('f1/' if f1 else '') + 'sla2_' + feat + '.csv')
	df = pd.read_csv(adapt_f, delimiter = ',' if f1 else '\t')
	print(df)
	df = df.set_index('Model')
	df = df.transpose()
	titles = {'sens': 'Sensitivity', 'cont': 'Contentiousness'}
	colors  = ['rosybrown', 'silver', 'steelblue', 'goldenrod']
	hatches = len(df) * ['-'] + len(df) * ['/'] + len(df) * [''] + len(df) * ['\\']
	ax = df.plot.bar(color = colors, figsize = (15,10), ylim=(0.5, 1.0), rot = 0, zorder=3)
	ax.grid(axis='y', zorder = 0)
	bars = ax.patches
	for bar, hatch in zip(bars, hatches):
		bar.set_hatch(hatch)
		bar.set_edgecolor('black')
	for tick in ax.xaxis.get_major_ticks():
		tick.label.set_fontsize(32)
	for tick in ax.yaxis.get_major_ticks():
		tick.label.set_fontsize(35)
	plt.xlabel("First SLO - Second SLO", fontsize = 35)
	plt.ylabel('F1 Score' if f1 else 'Accuracy', fontsize = 35)
	#ax.set_title(titles[feat], fontsize = 40)
#	ax.yaxis.set_label_coords(-0.06, 0.5)
	ax.xaxis.set_label_coords(0.5, -0.08)
	ax.legend(loc='upper center', frameon=False, fontsize = 30, ncol = 4)
	plt.tight_layout()
	plt.savefig('./sla_' + ('f1' if f1 else 'acc') + '_' + feat + '.png')

def graphs(args):
	if args[0] == 'v':
		try: sla = float(args[1])
		except: sla = 1.2
		return violation_bp(sla)
	if args[0] == 's2':
		try: feat = args[1]
		except: feat = 'sens'
		return multsla(feat)
	if args[0] == 'ex':
		return box_plot_example()
	if args[0] == 'c':
		try: feat = args[1]
		except: feat = 'sens'
		try: cc = int(args[2])
		except: cc = 2
		return box_plot_class(feat, cc)
	if args[0] == 'cvc':
		try: cc = int(args[1])
		except: cc = 2
		return bp_cvc(cc)
	if args[0] == 'ad':
		try: feat = args[1]
		except: feat = 'sens'
		try: cc = int(args[2])
		except: cc = 2
		return bar_plot_adapt(feat, cc)

if __name__ == '__main__':
	sys.exit(graphs(sys.argv[1:]))
