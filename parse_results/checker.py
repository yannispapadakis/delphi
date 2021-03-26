from base_config import *
from read_file import *
from shutil import copy2

def change(name):
	c = {'bzip': 'bzip2', 'sphinx': 'sphinx3', 'cactus': 'cactusADM'}
	if name in c:
		return c[name]
	return name

def early_end_cleanup(ldir, filename, times, which):
	scrap_path = '/home/ypap/scrap/'
	os.rename(ldir + filename, scrap_path + filename)
	old_fp = open(scrap_path + filename, 'r')
	new_fp = open(ldir + filename, 'w')
	line = old_fp.readline()
	heartbeats = len(times[which]) - 1
	i = 0
	while line:
		tokens = line.split(' - ')
		if 'EVENT' in line:
			try:
				event_data = tokens[2].replace('EVENT: ', '')
				json_data = json.loads(event_data)
				event_type = json_data['event']
				if event_type == 'heartbeat':
					if i >= heartbeats:
						line = old_fp.readline()
						continue
					else:
						i += 1
			except ValueError:
				pass
		new_fp.write(line)
		line = old_fp.readline()
	old_fp.close()
	new_fp.close()

def time_checker(filename, ldir):
	fp = open(ldir + filename)
	vms = map(lambda x: change(x.split('_')[0]), filename.split('.')[0].split('-'))
	vm_uuid = []
	times = dict()
	line = fp.readline()
	while line:
		tokens = line.split(' - ')
		if 'EVENT' in line:
			try:
				event_data = tokens[2].replace('EVENT: ','')
				json_data = json.loads(event_data)
				event_type = json_data['event']
				vm_seq_num = int(json_data['vm_seq_num'])
				now = datetime.datetime.strptime(json_data['time'], '%Y-%m-%d.%H:%M:%S')
				if event_type == 'boot':
					times[vm_seq_num] = [now]
				elif event_type == 'heartbeat':
					times[vm_seq_num].append(now)
			except ValueError:
				pass
		line = fp.readline()

	if times[0][-1] < times[1][-2]:
		early_end_cleanup(ldir, filename, times, 1)
	elif times[1][-1] < times[0][-2]:
		early_end_cleanup(ldir, filename, times, 0)
	if times[0][-1] < times[1][-2] or times[1][-1] < times[0][-2]:
		print filename, "END BEFORE PREVIOUS HEARTBEAT"
	else:
		non_overlap1 = (abs(times[0][-1] - times[1][-2])).total_seconds() / (abs(times[1][-1] - times[1][-2])).total_seconds()
		non_overlap2 = (abs(times[1][-1] - times[0][-2])).total_seconds() / (abs(times[0][-1] - times[0][-2])).total_seconds()
		non_overlap = non_overlap1 if times[0][-1] < times[1][-1] else non_overlap2
		if non_overlap < 0.2:
	#		print filename, "NOT ENOUGH OVERLAPPING:", non_overlap
			pass

def event_checker(filename, ldir):
	fp = open(ldir + filename)
	vms = map(lambda x: change(x.split('_')[0]), filename.split('.')[0].split('-'))
	vm_uuid = []
	vm_uuid_boot = []
	vm_uuid_hb = []
	line = fp.readline()
	valid = []
	while line:
		tokens = line.split(' - ')
		if '=> VM with uuid' in line:
			vm_uuid.append(line.split()[8])
		if 'EVENT' in line:
			try:
				event_data = tokens[2].replace('EVENT: ','')
				json_data = json.loads(event_data)
				event_type = json_data['event']
				vm_seq_num = json_data['vm_seq_num']
				if event_type == 'boot':
					vm_id = str(json_data['vm_uuid'])
					if vm_id not in vm_uuid_boot:
						vm_uuid_boot.append(vm_id)
				elif event_type == 'heartbeat':
					err_name = json_data['bench'].split('-')[1].split('.')[1]
					vm_id = str(json_data['vm_uuid'])
					if vm_id not in vm_uuid_hb:
						vm_uuid_hb.append(vm_id)
			except ValueError:
				pass
		if 'openstack_client' in line:
			if tokens[2].split()[-1] == 'ERROR)':
				print 'Vm with ERROR in:', filename
		if 'executor' in line:
			if 'failed to spawn with status ERROR' in line:
				print 'Vm with spawn ERROR in:', filename
		line = fp.readline()
	if len(vm_uuid) == 2:
		if len(vm_uuid_hb) != 2 or len(vm_uuid_boot) != 2:
			print filename, "From active:", len(vm_uuid), "From Boot:", len(vm_uuid_boot), "From HB:", len(vm_uuid_hb)
			valid = vm_uuid
	fp.close()
	return valid

def checker(ldir):
	valid_ids = {}
	for filename in os.listdir(ldir):
		valid = event_checker(filename, ldir)
		time_checker(filename, ldir)
		if valid:
			valid_ids[ldir + filename] = valid
	return valid_ids

def t_checker(ldir):
	for filename in os.listdir(ldir):
		time_checker(filename, ldir)

def cleanup(valid_ids):
	for filename in valid_ids:
		path = '/'.join(filename.split('/')[:-1]) + '/'
		new_file = filename.split('/')[-1].replace('-','.')
		valid = valid_ids[filename]
		old_fp = open(filename, 'r')
		new_fp = open(path + new_file, 'w')
		line = old_fp.readline()
		while line:
			tokens = line.split(' - ')
			if 'EVENT' in line:
				try:
					event_data = tokens[2].replace('EVENT: ', '')
					json_data = json.loads(event_data)
					event_type = json_data['event']
					if event_type == 'boot' or event_type == 'heartbeat' or event_type == 'shutdown':
						vm_id = str(json_data['vm_uuid'])
						if vm_id not in valid:
							line = old_fp.readline()
							continue
				except ValueError:
					pass
			new_fp.write(line)
			line = old_fp.readline()
		old_fp.close()
		new_fp.close()
		scrap_path = '/home/ypap/scrap/'
		os.rename(filename, scrap_path + filename.split('/')[-1])
		print filename, "is CLEAR!"

if __name__ == '__main__':
	for bench in os.listdir(pairs_dir):
		bench_dir = pairs + bench + '/' 
		for combination in os.listdir(bench_dir):
			ldir = bench_dir + combination + '/'
			t_checker(ldir)
			continue
			valid_ids = checker(ldir)
			cleanup(valid_ids)

