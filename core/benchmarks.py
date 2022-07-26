import random, re
benches_vcpus = {
	"spec-400.perlbench":
		{"is_noisy": 0, "is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 193.0, 2: 195.0, 4: 199.0, 8: 210.25}},
	"spec-401.bzip2":
		{"is_noisy": 0, "is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 128.0, 2: 124.5, 4: 125.5, 8: 129.125}},
	"spec-403.gcc":
		{"is_noisy": 0, "is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 23.0, 2: 23.0, 4: 24.0, 8: 24.625}},
	"spec-410.bwaves":
		{"is_noisy": 1, "is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 416.0, 2: 432.0, 4: 426.5, 8: 454.75}},
	"spec-416.gamess":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 62.0, 2: 349.5, 4: 364.25, 8: 374.75}},
	"spec-429.mcf":
		{"is_noisy": 1, "is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 272.0, 2: 295.5, 4: 373.75, 8: 455.125}},
	"spec-433.milc":
		{"is_noisy": 0,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 469.0, 2: 492.0, 4: 530.25, 8: 601.25}},
	"spec-434.zeusmp":
		{"is_noisy": 1,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 425.0, 2: 430.0, 4: 437.5, 8: 452.0}},
	"spec-435.gromacs":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 393.0, 2: 393.5, 4: 394.0, 8: 394.625}},
	"spec-436.cactusADM":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 660.0, 2: 668.0, 4: 705.75, 8: 847.5}},
	"spec-437.leslie3d":
		{"is_noisy": 0,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 325.0, 2: 343.0, 4: 366.25, 8: 442.875}},
	"spec-444.namd":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 457.0, 2: 457.0, 4: 458.0, 8: 456.625}},
	"spec-445.gobmk":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 82.0, 2: 82.5, 4: 84.0, 8: 82.875}},
	"spec-447.dealII":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 372.0, 2: 373.0, 4: 374.75, 8: 376.5}},
	"spec-450.soplex":
		{"is_noisy": 0,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 133.0, 2: 158.5, 4: 185.75, 8: 218.75}},
	"spec-453.povray":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 182.0, 2: 183.5, 4: 183.0, 8: 183.625}},
	"spec-454.calculix":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 892.0, 2: 892.0, 4: 893.5, 8: 893.75}},
	"spec-456.hmmer":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 152.0, 2: 151.0, 4: 152.0, 8: 151.625}},
	"spec-458.sjeng":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 629.0, 2: 631.5, 4: 634.25, 8: 635.125}},
	"spec-459.GemsFDTD":
		{"is_noisy": 1,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 380.0, 2: 401.0, 4: 419.75, 8: 522.625}},
	"spec-462.libquantum":
		{"is_noisy": 1,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 346.0, 2: 411.5, 4: 459.0,  8: 475.625}},
	"spec-464.h264ref":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 78.0, 2: 78.0, 4: 78.0, 8: 78.625}},
	"spec-465.tonto":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 621.0, 2: 376.0, 4: 253.25, 8: 250.0}},
	"spec-470.lbm":
		{"is_noisy": 1,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 407.0, 2: 414.0, 4: 452.25, 8: 707.25}},
	"spec-471.omnetpp":
		{"is_noisy": 0,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 301.0, 2: 366.5, 4: 440.5, 8: 502.5}},
	"spec-473.astar":
		{"is_noisy": 0, "is_sensitive": 0,
		 "run_mode": "to_completion","openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 170.0, 2: 179.0, 4: 197.75, 8: 215.5}}, 
	"spec-482.sphinx3":
		{"is_noisy": 1,	"is_sensitive": 1,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 621.0, 2: 630.0, 4: 658.5, 8: 807.375}},
	"spec-483.xalancbmk":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-image",
		 "runtime_isolation": {1: 234.0, 2: 253.0, 4: 291.5, 8: 339.25}},
	"parsec.blackscholes":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 257, 2: 142, 4: 82, 8: 53}},
	"parsec.bodytrack":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 813, 2: 430, 4: 226, 8: 128}},
	"parsec.canneal":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 327, 2: 196, 4: 125, 8: 91}},
	"parsec.dedup":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 53, 2: 36, 4: 25, 8: 12}},
	"parsec.facesim":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 2741, 2: 1424, 4: 761, 8: 411}},
	"parsec.ferret":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 883, 2: 575, 4: 288, 8: 143}},
	"parsec.fluidanimate":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 2389, 2: 1237, 4: 632, 8: 331}},
	"parsec.freqmine":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 553, 2: 282, 4: 141, 8: 71}},
	"parsec.streamcluster":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 1377, 2: 722, 4: 366, 8: 183}},
	"parsec.swaptions":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 595, 2: 300, 4: 149, 8: 74}},
	"parsec.vips":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 264, 2: 134, 4: 67, 8: 34}},
	"parsec.x264":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "acticloud-parsec",
		 "runtime_isolation": {1: 107, 2: 77, 4: 29, 8: 64}},
	"tailbench.img-dnn":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "parsec-tailbench",
		 "runtime_isolation": {1: 112, 2: 314, 4: 314, 8: 314},
		 "p95": {1: 0.662, 2: 0.742, 4: 0.739, 8: 0.777},
		 "p99": {1: 0.728, 2: 0.807, 4: 0.802, 8: 0.893}},
	"tailbench.masstree":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "parsec-tailbench",
		 "runtime_isolation": {2: 287, 8: 287},
		 "p95": {2: 0.561, 8: 0.780},
		 "p99": {2: 0.835, 8: 0.886}},
	"tailbench.moses":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "parsec-tailbench",
		 "runtime_isolation": {1: 305, 2: 306, 4: 306, 8: 306},
		 "p95": {1: 2.130, 2: 2.313, 4: 2.530, 8: 2.881},
		 "p99": {1: 2.499, 2: 2.599, 4: 2.809, 8: 3.186}},
	"tailbench.shore":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "parsec-tailbench",
		 "runtime_isolation": {2: 331, 4: 331, 8: 331},
		 "p95": {2: 4.229, 4: 4.056, 8: 3.830},
		 "p99": {2: 5.432, 4: 5.326, 8: 5.159}},
	"tailbench.silo":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "parsec-tailbench",
		 "runtime_isolation": {1: 246, 2: 247, 4: 247, 8: 247},
		 "p95": {1: 0.225, 2: 0.255, 4: 0.277, 8: 0.302},
		 "p99": {1: 0.300, 2: 0.370, 4: 0.384, 8: 0.661}},
	"tailbench.sphinx":
		{"is_noisy": 0,	"is_sensitive": 0,
		 "run_mode": "to_completion", "openstack_image": "parsec-tailbench",
		 "runtime_isolation": {1: 258, 2: 256, 4: 256, 8: 256},
		 "p95": {1: 1534.068, 2: 1570.260, 4: 1527.874, 8: 1530.911},
		 "p99": {1: 2071.398, 2: 2161.745, 4: 2387.787, 8: 1958.239}}
}

benches = [

#	{"name": "stress-stream",
#	 "is_noisy": 1,
#	 "is_sensitive": 1,
#	 "run_mode": "fixed_time",
#	 "openstack_image": "acticloud-image"},
#
#	## Moved the load as a random choice in `get_vm_userdata()`
#	{"name": "stress-cpu",
#	 "is_noisy": 0,
#	 "is_sensitive": 0,
#	 "run_mode": "fixed_time",
#	 "openstack_image": "acticloud-image"},

	{"name": "spec-400.perlbench",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 193},## The duration in seconds when run in isolation (1 vcpu)
	{"name": "spec-401.bzip2",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 126},
	{"name": "spec-403.gcc",		"is_noisy": 0,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 24},
	{"name": "spec-410.bwaves",		"is_noisy": 1,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 415},
	{"name": "spec-416.gamess",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 61},
	{"name": "spec-429.mcf",		"is_noisy": 1,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 274},
	{"name": "spec-433.milc",		"is_noisy": 0,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 465},
	{"name": "spec-434.zeusmp",		"is_noisy": 1,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 428},
	{"name": "spec-435.gromacs",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 393},
	{"name": "spec-436.cactusADM",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 666},
	{"name": "spec-437.leslie3d",	"is_noisy": 0,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 325},
	{"name": "spec-444.namd",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 458},
	{"name": "spec-445.gobmk",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 81},
	{"name": "spec-447.dealII",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 373},
	{"name": "spec-450.soplex",		"is_noisy": 0,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 133},
	{"name": "spec-453.povray",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 184},
	{"name": "spec-454.calculix",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 900},
	{"name": "spec-456.hmmer",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 152},
	{"name": "spec-458.sjeng",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 630},
	{"name": "spec-459.GemsFDTD",	"is_noisy": 1,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 380},
	{"name": "spec-462.libquantum",	"is_noisy": 1,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 358},
	{"name": "spec-464.h264ref",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 79},
	{"name": "spec-465.tonto",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 622},
	{"name": "spec-470.lbm",		"is_noisy": 1,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 407},
	{"name": "spec-471.omnetpp",	"is_noisy": 0,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 322},
	{"name": "spec-473.astar",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 169}, 
	{"name": "spec-482.sphinx3",	"is_noisy": 1,	"is_sensitive": 1,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 630},
	{"name": "spec-483.xalancbmk",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-image",	"runtime_isolation": 234},
	{"name": "parsec.blackscholes",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 257},
	{"name": "parsec.bodytrack",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 813},
	{"name": "parsec.canneal",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 327},
	{"name": "parsec.dedup",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 53},
	{"name": "parsec.facesim",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 2741},
	{"name": "parsec.ferret",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 883},
	{"name": "parsec.fluidanimate",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 2389},
	{"name": "parsec.freqmine",		"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 553},
	{"name": "parsec.streamcluster","is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 1377},
	{"name": "parsec.swaptions",	"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 595},
	{"name": "parsec.vips",			"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 264},
	{"name": "parsec.x264",			"is_noisy": 0,	"is_sensitive": 0,	"run_mode": "to_completion",	"openstack_image": "acticloud-parsec",	"runtime_isolation": 107},
]

benches_per_category = []
benches_per_category.append([x for x in benches if x['is_noisy'] == 0])
benches_per_category.append([x for x in benches if x['is_noisy'] == 1])

## The code to execute on newly created VMs in order to put load on them
def vm_user_data_header(custom_port):
	return """#!/bin/bash
export VMUUID=$(basename $(readlink -f /var/lib/cloud/instance)) ## Get VM's Openstack UUID
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"boot\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 """ + str(custom_port) + """
"""
def vm_user_data_footer(custom_port):
	return """
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"shutdown\\" , \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 """ + str(custom_port) + """
shutdown -h now
exit 0
"""
def vm_user_data_cpu(custom_port):
	return """
shutdown +$((%(runtime)d+5)) ## Just in case timeout stucks
timeout %(runtime)d bash -c \
'
i=0
while [ 1 ]; do
{
stress-ng -c %(vcpus)d -l %(load)d --timeout %(report_interval)d --metrics-brief
i=$((i+1))
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
       \\"bench\\": \\"stress-cpu\\", \\"load\\": %(load)d, \\"vcpus\\": %(vcpus)d, \
       \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \
       \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 """ + str(custom_port) + """
done
'
"""
def vm_user_data_stream(custom_port):
	return """
shutdown +$((%(runtime)d+5)) ## Just in case timeout stucks
timeout %(runtime)d bash -c \
'
i=0
while [ 1 ]; do
{
stress-ng --stream %(vcpus)d --timeout %(report_interval)d
sleep 10
i=$((i+1))
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
       \\"bench\\": \\"stress-stream\\", \\"vcpus\\": %(vcpus)d, \
       \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \
       \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 """ + str(custom_port) + """
done
'
"""
### The following is used by calculix spec benchmark to fix the problem we have with
### the cslab_interpret_spec_cmd.py file inside the VM
vm_user_data_calculix_fix_spec_interpret_line = \
"""
cd /opt/spec-parsec-benchmarks/spec/
sed -i 's/if "-i" in sys.argv:/if "-i" in sys.argv and not "calculix" in sys.argv[5]:/g' cslab_interpret_spec_cmd.py
"""
def vm_user_data_spec_to_completion(custom_port):
	return """
cd /opt/spec-parsec-benchmarks/spec/
for t in `seq 0 $((%(times_to_run)d-1))`; do
{
echo "EXECUTION NUMBER $t"
for i in `seq 0 $((%(vcpus)d-2))`; do
	./cslab_run_specs_static.sh %(bench)s $i &
	sleep 5 ## add this small sleep here because some benchmarks (e.g., calculix) have problems when spawned alltogether
done
./cslab_run_specs_static.sh %(bench)s $((%(vcpus)d-1))
wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
       \\"bench\\": \\"spec-%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \
       \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \
       \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 """ + str(custom_port) + """
done
"""
def vm_user_data_parsec_to_completion(custom_port):
	return """
cd /opt/parsec-benchmark/
source env.sh
for t in `seq 0 $((%(times_to_run)d-1))`; do
{
echo "EXECUTION NUMBER $t"
parsecmgmt -a run -p %(bench)s -i native -n $((%(vcpus)d)) > log/amd64-linux.gcc/run_output.out; tail -n 10 log/amd64-linux.gcc/run_output.out | head -n 1 | ./time_conversion.py
wait
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
       \\"bench\\": \\"%(bench)s-to-completion\\", \\"vcpus\\": %(vcpus)d, \
       \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \
       \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 """ + str(custom_port) + """
done
"""
def vm_user_data_spec_fixed_time(custom_port):
	return """
{
shutdown +$((%(runtime)d+5)) ## Just in case timeout stucks
cd /opt/spec-parsec-benchmarks/spec/
timeout %(runtime)d bash -c \
'
nr_executions=0
while [ 1 ]; do
	for i in `seq 0 $((%(vcpus)d-2))`; do
		./cslab_run_specs_static.sh %(bench)s $i &
	done
	./cslab_run_specs_static.sh %(bench)s $((%(vcpus)d-1))
	wait
	nr_executions=$(($nr_executions+1))
	echo NUMBER OF EXECUTIONS: $nr_executions
done
'
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
       \\"bench\\": \\"spec-%(bench)s-fixed-time\\", \\"vcpus\\": %(vcpus)d, \
       \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \
       \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 """ + str(custom_port) + """
"""
def vm_user_data_tailbench_fixed_time(custom_port):
	return """
{
shutdown +$((%(runtime)d+5)) ## Just in case timeout stucks
echo "-----> START: `date` VM number: %(seq_num)d name: tailbench-%(benchname)s runs TAILBENCH %(benchname)s"
cd /home/ubuntu
timeout %(runtime)d bash -c \
'
nr_executions=0
while [ 1 ]; do
	NTHREADS=%(vcpus)d ./run-bench.sh %(benchname)s
	nr_executions=$(($nr_executions+1))
	echo NUMBER OF EXECUTIONS: $nr_executions
done
'
echo "-----> END: VM number %(seq_num)d"
} &> /tmp/tosend
echo "{\\"vm_uuid\\": \\"$VMUUID\\", \\"vm_seq_num\\": %(seq_num)d, \\"event\\": \\"heartbeat\\", \
       \\"bench\\": \\"tailbench-%(benchname)s-fixed-time\\", \\"vcpus\\": %(vcpus)d, \
       \\"output\\": \\"`cat /tmp/tosend | tr \\"\\n\\" \\";\\" | tr \\"\\\\"\\" \\"^\\"`\\", \
       \\"time\\": \\"`date +%%F.%%T`\\"}" | nc -N 10.0.0.8 """ + str(custom_port) + """
"""

## bench -> dict()
def bench_get_name(bench):
	if bench[0] == "stress-cpu":
		load = random.choice([25, 50, 75, 100])
		bench['load'] = load
		return "stress-cpu-" + str(load)
	else:
		return bench[0]

## bench_name -> str, nvcpus -> int, output -> str
## returns float, the performance of the VM or -1 if the performance could not
## be obtained
def bench_get_perf_from_output(bench_name, nvcpus, output):
	ret = -1.0
	unit = "NULL"
	if bench_name == "stress-stream":
		memory_rate_entries = re.findall("memory rate: [0-9]*.[0-9]*", output)
		memory_rate_values = map(lambda x: float(x.split(':')[1]), memory_rate_entries)
		ret = sum(memory_rate_values) / len(memory_rate_values)
		unit = "throughput"
	elif "stress-cpu" in bench_name:
		bogoops_entry = re.findall("cpu +[0-9.]+ +[0-9.]+ +[0-9.]+ +[0-9.]+ +[0-9.]+ +[0-9.]+", output)[0]
		bogoops_value = bogoops_entry.split()[5]
		ret = bogoops_value
		unit = "throughput"
	elif "spec" in bench_name or "parsec" in bench_name:
		seconds_entries = re.findall("[0-9]+ seconds", output)
		seconds_values = map(lambda x: float(x.split()[0]), seconds_entries)
		ret = sum(seconds_values) / len(seconds_values)
		unit = "time"
	else:
		pass
	return (ret, unit)

## seq_num -> int, vcpus -> int, bench -> dict(), runtime -> int
def get_vm_userdata(seq_num, vcpus, bench, runtime, times_to_run, port):
	bench_name = bench[0]
	bench_run_mode = bench[1]['run_mode']

	report_interval = 1 * 60 # 1 minute
	runtime *= 60

	udata = vm_user_data_header(port) % {"seq_num": seq_num}
	if bench_name == "stress-cpu":
		load = bench['load']
		udata += vm_user_data_cpu(port) % {"seq_num": seq_num, "vcpus": vcpus,
		                             "runtime": runtime,
		                             "bench": bench, "load": load,
		                             "report_interval": report_interval}
	elif bench_name == "stress-stream":
		udata += vm_user_data_stream(port) % {"seq_num": seq_num, "vcpus": vcpus,
		                               "runtime": runtime,
		                               "report_interval": report_interval}
	elif "spec-" in bench_name:
		if "calculix" in bench_name:
			udata += vm_user_data_calculix_fix_spec_interpret_line

		spec_bench = bench_name.split("-")[1]
		udata += vm_user_data_spec_to_completion(port) % \
		                 {"seq_num": seq_num, "vcpus": vcpus,
		                  "times_to_run": times_to_run, "bench": spec_bench}
	elif "parsec" in bench_name:
		udata += vm_user_data_parsec_to_completion(port) % \
						 {"seq_num": seq_num, "vcpus": vcpus,
						  "times_to_run": times_to_run, "bench": bench_name}
	elif "tailbench-" in bench_name:
		tailbench = bench_name.split("-")[1]
		udata += vm_user_data_tailbench_fixed_time(port) % \
		             {"seq_num": seq_num, "vcpus": vcpus, "benchname": tailbench, \
		              "runtime": runtime}
	udata += vm_user_data_footer(port) % {"seq_num": seq_num}
	return udata
