#!/usr/bin/python
import datetime,sys,os,subprocess

def clean(filename):
	fp = open(filename)
	fw = open("output.txt", mode='w')
	line = fp.readline()
	while line:
		tokens = line.split(' - ')
		try:
			time = datetime.datetime.strptime(tokens[0], "%Y-%m-%d.%X")
		except:
			line = fp.readline()
			continue
		if tokens[2].startswith("Something"):
			line = fp.readline()
			continue
		if "EVENT" in line:
			event_data = tokens[2].replace("EVENT: ", "")
			if not event_data.startswith("{"):
				line = fp.readline()
				continue
		fw.write(line)
		line = fp.readline()
	fp.close()
	fw.close()
	os.rename('output.txt', filename)

def parse_all_files(folders):
	pairs_dir = '/home/ypap/delphi/results/coexecutions/'
	parsecs = subprocess.check_output('ls -rt ' + pairs_dir, shell = True).split("\n")[28:-1]
	if len(folders):
		if 'all' in folders: to_clean = parsecs
		else:
			for bench in folders:
				if bench not in parsecs:
					folders.pop(folders.index(bench))
			to_clean = folders
	for parsec in to_clean:
		for comb in os.listdir(pairs_dir + parsec):
			ld = pairs_dir + parsec + '/' + comb
			for filename in os.listdir(ld):
				clean(ld + '/' + filename)
		print parsec, "cleaned"
			
if __name__ == "__main__":
	parse_all_files(sys.argv[1:])
