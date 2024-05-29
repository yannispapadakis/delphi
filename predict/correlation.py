#!/usr/bin/python3
from isolation_reader import *

pqos = False
measures = read_perf_measures('')

apps = list(filter(lambda x: not x.startswith('Title'), measures.keys()))
corr = dict((app, dict((a, 0) for a in apps)) for app in apps)

ipc = 8 + int(pqos == True)
ipc_std = ipc + 14
for app1 in apps:
	for app2 in apps:
		app1_m = measures[app1][1:ipc] + measures[app1][(ipc + 1):ipc_std] + measures[app1][(ipc_std + 1):29]
		app2_m = measures[app2][1:ipc] + measures[app2][(ipc + 1):ipc_std] + measures[app2][(ipc_std + 1):29]
		#app1_m = measures[app1][15:29]
		#app2_m = measures[app2][15:29]
		corr[app1][app2] = np.corrcoef(app1_m, app2_m)[0,1]

ans = {}
for app in apps:
	disjoint = [appx for appx in apps if corr[appx][app] < 0.8]
	ans[app] = len(disjoint)

print(sorted(ans.items(), key = lambda x: x[1], reverse = True))
