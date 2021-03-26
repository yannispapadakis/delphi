import sys, os, json, datetime, random, time, re, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import numpy as np
import csv
from collections import OrderedDict
sys.path.insert(1, '/home/jim/jimsiak/actimanager')
import Billing

home_dir = '/'.join(os.getcwd().split('/')[:4]) + '/'
pairs_dir = home_dir + 'grid_runs/results/'
perf_dir = home_dir + 'perf_runs/results/'

silver_m = Billing.silver_money
gold_m = Billing.gold_money

def batch(slowdown):
	return silver_m / slowdown if slowdown < Billing.silver_tolerate else 0.0

def userfacing(gold, slowdown):
	if gold:
		return gold_m if slowdown < Billing.gold_tolerate else 0.0
	return silver_m if slowdown < Billing.silver_tolerate else 0.0

# Base perfs for benchmarks. Fill in any missing benchmarks
STRESS_CPU_ISOLATION = { 1: {25: 50.13,  50: 100.38, 75: 150.6, 100: 201.96},
						 2: {25: 100.27, 50: 200.35, 75: 301.3, 100: 403.72},
						 4: {25: 200.82, 50: 401.92, 75: 603.5, 100: 807.33},
						 8: {25: 406.11, 50: 803.13, 75: 1206.10, 100:1614.66} }
STRESS_STREAM_ISOLATION = { 1: 10727.72, 2: 9138.285, 4: 8414.2375, 8: 6808.85 }

SPEC_ISOLATION = {	'459.GemsFDTD': {1: 381.0, 2: 401.0, 4: 419.75, 8: 522.625},
					'473.astar': {1: 171.0, 2: 179.0, 4: 197.75, 8: 215.5},
					'410.bwaves': {1: 417.0, 2: 420.0, 4: 426.5, 8: 454.75},
					'401.bzip2': {1: 126.0, 2: 125.0, 4: 125.5, 8: 129.125},
					'436.cactusADM': {1: 664.0, 2: 668.0, 4: 705.75, 8: 847.5},
					'454.calculix': {1: 892.0, 2: 892.0, 4: 893.5, 8: 893.75},
					'447.dealII': {1: 372.0, 2: 373.0, 4: 374.75, 8: 376.5},
					'416.gamess': {1: 60.0, 2: 349.5, 4: 364.25, 8: 374.75},
					'403.gcc': {1: 23.0, 2: 22.75, 4: 24.0, 8: 24.625},
					'445.gobmk': {1: 82.0, 2: 82.5, 4: 84.0, 8: 82.875},
					'435.gromacs': {1: 394.0, 2: 393.5, 4: 394.0, 8: 394.625},
					'464.h264ref': {1: 78.0, 2: 78.0, 4: 78.0, 8: 78.625},
					'456.hmmer': {1: 152.0, 2: 151.0, 4: 152.0, 8: 151.625},
					'470.lbm': {1: 408.0, 2: 414.0, 4: 452.25, 8: 707.25},
					'437.leslie3d': {1: 330.0, 2: 343.0, 4: 366.25, 8: 442.875},
					'462.libquantum': {1: 349.0, 2: 411.5, 4: 459.0, 8: 475.625},
					'429.mcf': {1: 274.0, 2: 295.5, 4: 373.75, 8: 455.125},
					'433.milc': {1: 463.0, 2: 492.0, 4: 530.25, 8: 601.25},
					'444.namd': {1: 458.0, 2: 457.0, 4: 458.0, 8: 456.625},
					'471.omnetpp': {1: 291.0, 2: 366.5, 4: 440.5, 8: 502.5},
					'400.perlbench': {1: 194.0, 2: 194.0, 4: 199.0, 8: 210.25},
					'453.povray': {1: 184.0, 2: 183.5, 4: 183.0, 8: 183.625},
					'458.sjeng': {1: 628.0, 2: 631.5, 4: 634.25, 8: 635.125},
					'450.soplex': {1: 135.0, 2: 158.5, 4: 185.75, 8: 218.75},
					'482.sphinx3': {1: 623.0, 2: 630.0, 4: 658.5, 8: 807.375},
					'465.tonto': {1: 621.0, 2: 376.0, 4: 253.25, 8: 250.0},
					'483.xalancbmk': {1: 236.0, 2: 253.0, 4: 291.5, 8: 339.25},
					'434.zeusmp': {1: 423.0, 2: 430.0, 4: 437.5, 8: 452.0}}

save_graph_dir = home_dir + 'workload/results/graphs/'
save_csv_dir = home_dir + 'workload/results/csv_outputs/'

# For perVM plots
colors = ['black', 'red', 'green', 'blue', 'magenta']
markers = ['s', 'o', '^', 'X', 'x']
sizes = [10,9,8,7,6]

# Tags to replace the scenarios' names for cleaner look
replace = {'vanilla_openstack': 'Openstack', 'gold_socket_isolation': 'Socket', 'gps': 'Socket',
		   'gold_not_oversubscribed': 'GNO', 'gno': "GNO",
		   'actistatic': 'ACTiManager Static', 'actimanager_static': 'ACTiManager Static',
		   'actifull': 'ACTiManager Dynamic'}

