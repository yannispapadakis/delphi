import sys, time, math, datetime, signal, calendar, logging, subprocess, os, random, re, json, csv, pprint, math
import numpy as np
from scipy.stats.mstats import gmean
from itertools import product
from operator import add, itemgetter
from collections import OrderedDict
from vm_messages_monitor import *

import event_logger

home_dir = '/'.join(os.getcwd().split('/')[:4]) + '/'
results_dir = home_dir + 'results/'
coexecutions_dir = results_dir + 'coexecutions/'
isolation_dir = results_dir + 'isolation_runs/'
heatmap_dir = results_dir + 'heatmaps/'
predictions_dir = results_dir + 'predictions/'
gridsearch_dir = results_dir + 'GridSearch/'
graphs_dir = results_dir + 'graphs/'
violations_dir = results_dir + 'violations/'
workload_dir = home_dir + 'pairings/workload_pairs/'

vcpus = ['1', '2', '4', '8']
qos_levels = [1 + 0.1 * x for x in range(1, 4)]
classes_ = [2, 3]
features = ['sens', 'cont']
functions = ['cv', 'test']
models = ['LR', 'SGD', 'PA', 'PER', 'RID', 'LDA', 'QDA', 'SVC', \
		  'DT', 'KN', 'RN', 'NC', 'GP', 'GNB', 'RF', 'ET', 'AB', 'GB', 'MLP']
chosen_models = ['ET', 'RF', 'GB', 'MLP']

p95 = False
excluded_benchmarks = ['shore-1', 'masstree-8']

benches_vcpus = {
	"spec-400.perlbench":	{"runtime_isolation": {1: 193.0, 2: 195.0, 4: 199.0, 8: 210.25}},
	"spec-401.bzip2":		{"runtime_isolation": {1: 128.0, 2: 124.5, 4: 125.5, 8: 129.125}},
	"spec-403.gcc":			{"runtime_isolation": {1: 23.0, 2: 23.0, 4: 24.0, 8: 24.625}},
	"spec-410.bwaves":		{"runtime_isolation": {1: 416.0, 2: 432.0, 4: 426.5, 8: 454.75}},
	"spec-416.gamess":		{"runtime_isolation": {1: 62.0, 2: 349.5, 4: 364.25, 8: 374.75}},
	"spec-429.mcf":			{"runtime_isolation": {1: 287.0, 2: 295.5, 4: 373.75, 8: 455.125}},
	"spec-433.milc":		{"runtime_isolation": {1: 469.0, 2: 513.0, 4: 530.25, 8: 601.25}},
	"spec-434.zeusmp":		{"runtime_isolation": {1: 425.0, 2: 430.0, 4: 437.5, 8: 452.0}},
	"spec-435.gromacs":		{"runtime_isolation": {1: 393.0, 2: 393.5, 4: 394.0, 8: 394.625}},
	"spec-436.cactusADM":	{"runtime_isolation": {1: 660.0, 2: 668.0, 4: 705.75, 8: 847.5}},
	"spec-437.leslie3d":	{"runtime_isolation": {1: 325.0, 2: 343.0, 4: 366.25, 8: 442.875}},
	"spec-444.namd":		{"runtime_isolation": {1: 457.0, 2: 457.0, 4: 458.0, 8: 456.625}},
	"spec-445.gobmk":		{"runtime_isolation": {1: 82.0,	2: 82.5, 4: 84.0, 8: 82.875}},
	"spec-447.dealII":		{"runtime_isolation": {1: 372.0, 2: 373.0, 4: 374.75, 8: 376.5}},
	"spec-450.soplex":		{"runtime_isolation": {1: 133.0, 2: 158.5, 4: 185.75, 8: 218.75}},
	"spec-453.povray":		{"runtime_isolation": {1: 182.0, 2: 183.5, 4: 183.0, 8: 183.625}},
	"spec-454.calculix":	{"runtime_isolation": {1: 892.0, 2: 892.0, 4: 893.5, 8: 893.75}},
	"spec-456.hmmer":		{"runtime_isolation": {1: 152.0, 2: 151.0, 4: 152.0, 8: 151.625}},
	"spec-458.sjeng":		{"runtime_isolation": {1: 629.0, 2: 631.5, 4: 634.25, 8: 635.125}},
	"spec-459.GemsFDTD":	{"runtime_isolation": {1: 380.0, 2: 401.0, 4: 419.75, 8: 522.625}},
	"spec-462.libquantum":	{"runtime_isolation": {1: 346.0, 2: 411.5, 4: 459.0, 8: 708.25}},
	"spec-464.h264ref":		{"runtime_isolation": {1: 78.0,	2: 78.0, 4: 78.0, 8: 78.625}},
	"spec-465.tonto":		{"runtime_isolation": {1: 621.0, 2: 376.0, 4: 253.25, 8: 250.0}},
	"spec-470.lbm":			{"runtime_isolation": {1: 407.0, 2: 414.0, 4: 452.25, 8: 707.25}},
	"spec-471.omnetpp":		{"runtime_isolation": {1: 301.0, 2: 398.0, 4: 440.5, 8: 502.5}},
	"spec-473.astar":		{"runtime_isolation": {1: 181.0, 2: 179.0, 4: 198.0, 8: 215.5}},
	"spec-482.sphinx3":		{"runtime_isolation": {1: 621.0, 2: 630.0, 4: 658.5, 8: 807.375}},
	"spec-483.xalancbmk":	{"runtime_isolation": {1: 238.0, 2: 256.0, 4: 308.5, 8: 347.5}},
	"parsec.blackscholes":	{"runtime_isolation": {1: 257, 2: 142, 4: 82, 8: 53}},
	"parsec.bodytrack":		{"runtime_isolation": {1: 813, 2: 430, 4: 226, 8: 128}},
	"parsec.canneal":		{"runtime_isolation": {1: 277, 2: 179, 4: 112, 8: 84}},
	"parsec.dedup":			{"runtime_isolation": {1: 68, 2: 36, 4: 20, 8: 13}},
	"parsec.facesim":		{"runtime_isolation": {1: 2741, 2: 1424, 4: 761, 8: 411}},
	"parsec.ferret":		{"runtime_isolation": {1: 1137, 2: 575, 4: 288, 8: 143}},
	"parsec.fluidanimate":	{"runtime_isolation": {1: 2389, 2: 1237, 4: 632, 8: 331}},
	"parsec.freqmine":		{"runtime_isolation": {1: 553, 2: 282, 4: 141, 8: 71}},
	"parsec.streamcluster":	{"runtime_isolation": {1: 1377, 2: 676, 4: 341, 8: 172}},
	"parsec.swaptions":		{"runtime_isolation": {1: 595, 2: 300, 4: 149, 8: 74}},
	"parsec.vips":			{"runtime_isolation": {1: 264, 2: 134, 4: 67, 8: 34}},
	"parsec.x264":			{"runtime_isolation": {1: 108, 2: 77, 4: 29, 8: 64}},
	"tailbench.img-dnn":	{"runtime_isolation": {1: 299, 2: 300, 4: 299, 8: 299},
							 "p95": {1: 0.795, 2: 0.822, 4: 0.837, 8: 0.932},
							 "p99": {1: 0.846, 2: 1.338, 4: 1.010, 8: 1.112}},
	"tailbench.masstree":	{"runtime_isolation": {1: 296, 2: 296, 4: 296, 8: 287},
							 "p95": {1: 0.456, 2: 0.500, 4: 0.468, 8: 0.780},
							 "p99": {1: 0.526, 2: 0.577, 4: 0.609, 8: 0.886}},
	"tailbench.moses":		{"runtime_isolation": {1: 305, 2: 306, 4: 306, 8: 306},
							 "p95": {1: 2.130, 2: 2.313, 4: 2.530, 8: 2.881},
							 "p99": {1: 2.499, 2: 2.599, 4: 2.809, 8: 3.186}},
	"tailbench.shore":		{"runtime_isolation": {2: 331, 4: 331, 8: 331},
							 "p95": {2: 4.229, 4: 4.056, 8: 3.830},
							 "p99": {2: 5.432, 4: 5.326, 8: 5.159}},
	"tailbench.silo":		{"runtime_isolation": {1: 246, 2: 247, 4: 247, 8: 247},
							 "p95": {1: 0.225, 2: 0.255, 4: 0.277, 8: 0.302},
							 "p99": {1: 0.300, 2: 0.370, 4: 0.384, 8: 0.661}},
	"tailbench.sphinx":		{"runtime_isolation": {1: 258, 2: 256, 4: 256, 8: 256},
							 "p95": {1: 1534.068, 2: 1570.260, 4: 1527.874, 8: 1530.911},
							 "p99": {1: 2071.398, 2: 2161.745, 4: 2387.787, 8: 1958.239}},
	"iperf3":				{"runtime_isolation": {1: 300},
							 "bw": {1: 16577350000.0}}
}

specs = [x + '-' + y for x in map(lambda x: x.split('.')[1], filter(lambda x: 'spec' in x, benches_vcpus.keys())) for y in vcpus]
parsecs = [x + '-' + y for x in map(lambda x: x.split('.')[1], filter(lambda x: 'parsec' in x, benches_vcpus.keys())) for y in vcpus]
tails = list(filter(lambda x: x not in excluded_benchmarks,
			[x + '-' + y for x in map(lambda x: x.split('.')[1], filter(lambda x: 'tailbench' in x, benches_vcpus.keys())) for y in vcpus]))
tails = list(map(lambda x: x if 'sphinx' not in x else 'tailbench.' + x, tails))
benchmark_suites = {'s': specs, 'p': parsecs, 't': tails}

##################### Execution configs ##################### 
## Setup the logging facility
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(message)s', datefmt='%Y-%m-%d.%H:%M:%S')
logging.Formatter.converter = time.gmtime
logger = logging.getLogger("executor")

#vm_messages_monitor = None
PORT = 8081
vm_messages_monitor = VmMessagesMonitor(port=PORT)

def signal_handler(signum, frame):
	logger.info("-> Caught a signal, exiting...")
	vm_messages_monitor.stop_monitor_thread()
	sys.exit(1)
############################################################# 

vm_header = \
"""export VMUUID=$(basename $(readlink -f /var/lib/cloud/instance)); echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"boot\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d;"""

client_header = \
"""export SUUID=%(suuid)s; export VMUUID=$(basename $(readlink -f /var/lib/cloud/instance)); echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"boot\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d;"""

vm_footer = \
"""echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"shutdown\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d; exit 0"""

vm_calculix = \
"""cd /opt/spec-parsec-benchmarks/spec/; sed -i 's/if "-i" in sys.argv:/if "-i" in sys.argv and not "calculix" in sys.argv[5]:/g' cslab_interpret_spec_cmd.py;"""

vm_spec = \
"""cd /opt/spec-parsec-benchmarks/spec/
for t in `seq 0 $((%(times_to_run)d-1))`; do 
{
	echo "EXECUTION NUMBER $t"
	for i in `seq 0 $((%(vcpus)d-2))`; do
		./cslab_run_specs_static.sh %(bench)s $i &
		sleep 5
	done
	./cslab_run_specs_static.sh %(bench)s $((%(vcpus)d-1))
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"spec-%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
done
"""

vm_parsec = \
"""cd /opt/parsec-benchmark/
source env.sh
for t in `seq 0 $((%(times_to_run)d-1))`; do 
{
	echo "EXECUTION NUMBER $t"
	parsecmgmt -a run -p %(bench)s -i native -n $((%(vcpus)d)) > log/amd64-linux.gcc/run_output.out; tail -n 10 log/amd64-linux.gcc/run_output.out | head -n 1 | ./time_conversion.py
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
done
"""

spec_extra = \
"""cd /opt/spec-parsec-benchmarks/spec/
{
	for i in `seq 0 $((%(vcpus)d-2))`; do
		./cslab_run_specs_static.sh %(bench)s $i &
		sleep 5
	done
	./cslab_run_specs_static.sh %(bench)s $((%(vcpus)d-1))
	wait
} &> /tmp/tosend
"""

parsec_extra = \
"""cd /opt/parsec-benchmark/
source env.sh
{
	parsecmgmt -a run -p %(bench)s -i native -n $((%(vcpus)d)) > log/amd64-linux.gcc/run_output.out
	wait
} &> /tmp/tosend
"""

tailbench_server = \
"""cd /opt/tailbench-v0.9
for t in `seq 0 $((%(times_to_run)d-1))`; do
{
	echo "EXECUTION NUMBER $t"
	./server_run.sh %(bench)s
	wait
} &> /tmp/tosend
done
"""

tailbench_client = \
"""cd /opt/tailbench-v0.9
for t in `seq 0 $((%(times_to_run)d-1))`; do
{
	echo "EXECUTION NUMBER $t"
	./client_run.sh %(bench)s %(ip)s
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$SUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"tailbench.%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
done
"""
tailbench_client_extra = \
"""cd /opt/tailbench-v0.9
{
	echo "EXECUTION NUMBER +1"
	./client_run.sh %(bench)s %(ip)s
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$SUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"tailbench.%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
"""

iperf_server = \
"""for t in `seq 0 $((%(times_to_run)d-1))`; do
{
	echo "EXECUTION NUMBER $t"
	sleep 2
	rm -f output.json
	iperf3 -s -A 0 -1 --logfile output.json -J; ./iperf_reader.py
	wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
\\"bench\\": \\"iperf3-to-completion\\", \\"vcpus\\": 1, \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 %(port)d
done
"""

iperf_client = \
"""for t in `seq 0 $((%(times_to_run)d-1))`; do
{
	sleep 4
	iperf3 -c 10.0.100.%(ip)s -t 300
	wait
} &> /dev/null
done
"""
