#!/usr/bin/env python



import os, sys, traceback
import getpass
from threading import Thread
from subprocess import *

if(sys.hexversion < 0x03000000):
	import Queue
else:
	import queue as Queue

svmtrain_exe = "svm-train"

# global parameters and their default values

fold = 5
c_begin, c_end, c_step = -5,  15, 2
g_begin, g_end, g_step =  3, -15, -2
global dataset_pathname, dataset_title, pass_through_string
global out_filename, png_filename

# experimental

telnet_workers = []
ssh_workers = []
nr_local_worker = 4

# process command line options, set global parameters
def process_options(argv=sys.argv):

    global fold
    global c_begin, c_end, c_step
    global g_begin, g_end, g_step
    global dataset_pathname, dataset_title, pass_through_string
    global svmtrain_exe, out_filename, png_filename
    
    usage = """\
Usage: grid.py [-log2c begin,end,step] [-log2g begin,end,step] [-v fold] 
[-svmtrain pathname] [-out pathname] [-png pathname]
[additional parameters for svm-train] dataset"""

    if len(argv) < 2:
        print(usage)
        sys.exit(1)

    dataset_pathname = argv[-1]
    out_filename = '%s.out' % dataset_pathname
    png_filename = '%s.png' % dataset_pathname
    pass_through_options = []

    i = 1
    while i < len(argv) - 1:
        if argv[i] == "-log2c":
            i = i + 1
            (c_begin,c_end,c_step) = map(float,argv[i].split(","))
        elif argv[i] == "-log2g":
            i = i + 1
            (g_begin,g_end,g_step) = map(float,argv[i].split(","))
        elif argv[i] == "-v":
            i = i + 1
            fold = argv[i]
        elif argv[i] in ('-c','-g'):
            print("Option -c and -g are renamed.")
            print(usage)
            sys.exit(1)
        elif argv[i] == '-svmtrain':
            i = i + 1
            svmtrain_exe = argv[i]
        elif argv[i] == '-out':
            i = i + 1
            out_filename = argv[i]
        elif argv[i] == '-png':
            i = i + 1
            png_filename = argv[i]
        else:
            pass_through_options.append(argv[i])
        i = i + 1

    pass_through_string = " ".join(pass_through_options)
    assert os.path.exists(dataset_pathname),"dataset not found"
    #gnuplot = Popen(gnuplot_exe,stdin = PIPE).stdin


def range_f(begin,end,step):
    # like range, but works on non-integer too
    seq = []
    while True:
        if step > 0 and begin > end: break
        if step < 0 and begin < end: break
        seq.append(begin)
        begin = begin + step
    return seq

def permute_sequence(seq):
    n = len(seq)
    if n <= 1: return seq

    mid = int(n/2)
    left = permute_sequence(seq[:mid])
    right = permute_sequence(seq[mid+1:])

    ret = [seq[mid]]
    while left or right:
        if left: ret.append(left.pop(0))
        if right: ret.append(right.pop(0))

    return ret

def redraw(db,best_param,tofile=False):
    if len(db) == 0: return
    begin_level = round(max(x[2] for x in db)) - 3
    step_size = 0.5

    best_log2c,best_log2g,best_rate = best_param

    #if tofile:
        #gnuplot.write( "set term png transparent small\n".encode())
        #gnuplot.write( ("set output \"%s\"\n" % png_filename.replace('\\','\\\\')).encode())
        #gnuplot.write("set term postscript color solid\n".encode())
        #gnuplot.write(("set output \"%s.ps\"\n" % dataset_title).encode())
    #elif is_win32:
        #gnuplot.write("set term windows\n".encode())
    #else:
        #gnuplot.write( "set term x11\n".encode())
    #gnuplot.write("set xlabel \"log2(C)\"\n".encode())
    #gnuplot.write("set ylabel \"log2(gamma)\"\n".encode())
    #gnuplot.write(("set xrange [%s:%s]\n" % (c_begin,c_end)).encode())
    #gnuplot.write(("set yrange [%s:%s]\n" % (g_begin,g_end)).encode())
    #gnuplot.write("set dgrid3d 50,50\n".encode())
    #gnuplot.write("set contour\n".encode())
    #gnuplot.write(("set cntrparam levels incremental %s,%s,100\n" % (begin_level,step_size)).encode())
    #gnuplot.write("unset surface\n".encode())
    #gnuplot.write("unset ztics\n".encode())
    #gnuplot.write("set view 0,0\n".encode())
    #gnuplot.write(("set title \"%s\"\n" % dataset_title).encode())
    #gnuplot.write("unset label\n".encode())
    #gnuplot.write(("set label \"Best log2(C) = %s  log2(gamma) = %s  accuracy = %s%%\" \
    #              at screen 0.5,0.85 center\n" % \
    #              (best_log2c, best_log2g, best_rate)).encode())
    #gnuplot.write(("set label \"C = %s  gamma = %s\""
    #              " at screen 0.5,0.8 center\n" % (2**best_log2c, 2**best_log2g)).encode())
    #gnuplot.write("splot \"-\" with lines\n".encode())
    
    


    
    db.sort(key = lambda x:(x[0], -x[1]))

    #prevc = db[0][0]
    #for line in db:
    #    if prevc != line[0]:
    #        gnuplot.write("\n".encode())
    #        prevc = line[0]
    #    gnuplot.write(("%s %s %s\n" % line).encode())
    #gnuplot.write("e\n".encode())
    #gnuplot.write("\n".encode()) # force gnuplot back to prompt when term set failure
    #gnuplot.flush()


def calculate_jobs():
    c_seq = permute_sequence(range_f(c_begin,c_end,c_step))
    g_seq = permute_sequence(range_f(g_begin,g_end,g_step))
    nr_c = float(len(c_seq))
    nr_g = float(len(g_seq))
    i = 0
    j = 0
    jobs = []

    while i < nr_c or j < nr_g:
        if i/nr_c < j/nr_g:
            # increase C resolution
            line = []
            for k in range(0,j):
                line.append((c_seq[i],g_seq[k]))
            i = i + 1
            jobs.append(line)
        else:
            # increase g resolution
            line = []
            for k in range(0,i):
                line.append((c_seq[k],g_seq[j]))
            j = j + 1
            jobs.append(line)
    return jobs

class WorkerStopToken:  # used to notify the worker to stop
        pass

class Worker(Thread):
    def __init__(self,name,job_queue,result_queue):
        Thread.__init__(self)
        self.name = name
        self.job_queue = job_queue
        self.result_queue = result_queue
    def run(self):
        while True:
            (cexp,gexp) = self.job_queue.get()
            if cexp is WorkerStopToken:
                self.job_queue.put((cexp,gexp))
                # print 'worker %s stop.' % self.name
                break
            try:
                rate = self.run_one(2.0**cexp,2.0**gexp)
                if rate is None: raise "get no rate"
            except:
                # we failed, let others do that and we just quit
            
                traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
                
                self.job_queue.put((cexp,gexp))
                print('worker %s quit.' % self.name)
                break
            else:
                self.result_queue.put((self.name,cexp,gexp,rate))

class LocalWorker(Worker):
    def run_one(self,c,g):
        cmdline = '%s -c %s -g %s -v %s %s %s' % \
          (svmtrain_exe,c,g,fold,pass_through_string,dataset_pathname)
        result = Popen(cmdline,shell=True,stdout=PIPE).stdout
        for line in result.readlines():
            if str(line).find("Cross") != -1:
                return float(line.split()[-1][0:-1])

class SSHWorker(Worker):
    def __init__(self,name,job_queue,result_queue,host):
        Worker.__init__(self,name,job_queue,result_queue)
        self.host = host
        self.cwd = os.getcwd()
    def run_one(self,c,g):
        cmdline = 'ssh -x %s "cd %s; %s -c %s -g %s -v %s %s %s"' % \
          (self.host,self.cwd,
           svmtrain_exe,c,g,fold,pass_through_string,dataset_pathname)
        result = Popen(cmdline,shell=True,stdout=PIPE).stdout
        for line in result.readlines():
            if str(line).find("Cross") != -1:
                return float(line.split()[-1][0:-1])

class TelnetWorker(Worker):
    def __init__(self,name,job_queue,result_queue,host,username,password):
        Worker.__init__(self,name,job_queue,result_queue)
        self.host = host
        self.username = username
        self.password = password        
    def run(self):
        import telnetlib
        self.tn = tn = telnetlib.Telnet(self.host)
        tn.read_until("login: ")
        tn.write(self.username + "\n")
        tn.read_until("Password: ")
        tn.write(self.password + "\n")

        # XXX: how to know whether login is successful?
        tn.read_until(self.username)
        # 
        print('login ok', self.host)
        tn.write("cd "+os.getcwd()+"\n")
        Worker.run(self)
        tn.write("exit\n")               
    def run_one(self,c,g):
        cmdline = '%s -c %s -g %s -v %s %s %s' % \
          (svmtrain_exe,c,g,fold,pass_through_string,dataset_pathname)
        result = self.tn.write(cmdline+'\n')
        (idx,matchm,output) = self.tn.expect(['Cross.*\n'])
        for line in output.split('\n'):
            if str(line).find("Cross") != -1:
                return float(line.split()[-1][0:-1])

def main():

    # set parameters

    process_options()

    # put jobs in queue

    jobs = calculate_jobs()
    job_queue = Queue.Queue(0)
    result_queue = Queue.Queue(0)

    for line in jobs:
        for (c,g) in line:
            job_queue.put((c,g))

    job_queue._put = job_queue.queue.appendleft


    # fire telnet workers

    if telnet_workers:
        nr_telnet_worker = len(telnet_workers)
        username = getpass.getuser()
        password = getpass.getpass()
        for host in telnet_workers:
            TelnetWorker(host,job_queue,result_queue,
                     host,username,password).start()

    # fire ssh workers

    if ssh_workers:
        for host in ssh_workers:
            SSHWorker(host,job_queue,result_queue,host).start()

    # fire local workers

    for i in range(nr_local_worker):
        LocalWorker('local',job_queue,result_queue).start()

    # gather results

    done_jobs = {}


    result_file = open(out_filename, 'w')


    db = []
    best_rate = -1
    best_c1,best_g1 = None,None

    for line in jobs:
        for (c,g) in line:
            while (c, g) not in done_jobs:
                (worker,c1,g1,rate) = result_queue.get()
                done_jobs[(c1,g1)] = rate
                result_file.write('%s %s %s\n' %(c1,g1,rate))
                result_file.flush()
                if (rate > best_rate) or (rate==best_rate and g1==best_g1 and c1<best_c1):
                    best_rate = rate
                    best_c1,best_g1=c1,g1
                    best_c = 2.0**c1
                    best_g = 2.0**g1
                print("[%s] %s %s %s (best c=%s, g=%s, rate=%s)" % \
		    (worker,c1,g1,rate, best_c, best_g, best_rate))
            db.append((c,g,done_jobs[(c,g)]))
        redraw(db,[best_c1, best_g1, best_rate])
        redraw(db,[best_c1, best_g1, best_rate],True)

    job_queue.put((WorkerStopToken,None))
    print("%s %s %s" % (best_c, best_g, best_rate))
main()
