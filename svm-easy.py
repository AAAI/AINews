#!/usr/bin/env python

import sys
import os
from subprocess import *

if len(sys.argv) <= 1:
	print('Usage: %s training_file [testing_file]' % sys.argv[0])
	raise SystemExit

svmscale_exe = "svm-scale"
svmtrain_exe = "svm-train"
svmpredict_exe = "svm-predict"
grid_py = "./svm-grid.py"

train_pathname = sys.argv[1]
assert os.path.exists(train_pathname),"training file not found"
scaled_file = train_pathname + ".scale"
model_file = train_pathname + ".model"
range_file = train_pathname + ".range"

if len(sys.argv) > 2:
	test_pathname = sys.argv[2]
	assert os.path.exists(test_pathname),"testing file not found"
	scaled_test_file = test_pathname + ".scale"
	predict_test_file = test_pathname + ".predict"

cmd = '%s -l 0 -u 1 -s "%s" "%s" > "%s"' % (svmscale_exe, range_file, train_pathname, scaled_file)
print('Scaling training data...')
Popen(cmd, shell = True).wait()

cmd = '%s -svmtrain "%s" "%s"' % (grid_py, svmtrain_exe, scaled_file)
print('Cross validation...')
f = Popen(cmd, shell = True, stdout = PIPE).stdout

line = ''
while True:
	last_line = line
	line = f.readline()
	if not line: break
c,g,rate = map(float,last_line.split())

print('Best c=%s, g=%s CV rate=%s' % (c,g,rate))

cmd = '%s -b 1 -t 0 -c %s -g %s "%s" "%s"' % (svmtrain_exe,c,g,scaled_file,model_file)
#cmd = '%s -b 1 -log2c -1,2,1 -log2g 1,1,1 -t 0  "%s" "%s"' % (svmtrain_exe,scaled_file,model_file)
print('Training...')
Popen(cmd, shell = True).wait()

print('Output model: %s' % model_file)
if len(sys.argv) > 2:
	cmd = '%s -r "%s" "%s" > "%s"' % (svmscale_exe, range_file, test_pathname, scaled_test_file)
	print('Scaling testing data...')
	Popen(cmd, shell = True).wait()

	cmd = '%s "%s" "%s" "%s"' % (svmpredict_exe, scaled_test_file, model_file, predict_test_file)
	print('Testing...')
	Popen(cmd, shell = True).wait()

	print('Output prediction: %s' % predict_test_file)

