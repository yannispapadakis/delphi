#!/usr/bin/python3
from predictor import *

def parsec_test(args):
	func = ['test']
	features = ['sens', 'cont']
	qos_ = [float(args[0])]
	classes = [int(args[1])]
	test_space = [func, features, qos_, classes, models]
	for grid_point in list(product(*test_space)):
		if 'BAG' not in grid_point:
			prediction(grid_point)

if __name__ == '__main__':
	parsec_test(sys.argv[1:])
