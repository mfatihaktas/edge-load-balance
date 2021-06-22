from debug_utils import *

def run(node_l, cmd_l):
	popens = {}
	for i, n in enumerate(node_l):
		popens[n] = n.popen(cmd_l[i])
		log(DEBUG, "Started {}".format(n))

def run_masters(m_l):
	run(m_l, ['./run.sh m {}'.format(i) for i in range(len(m_l))])
	log(DEBUG, "done")

def run_workers(w_l):
	run(w_l, ['./run.sh w {}'.format(i) for i in range(len(w_l))])
	log(DEBUG, "done")

def run_dashboard_server(d):
	run([d], ['./run.sh d'])
	log(DEBUG, "done")

# TODO: does not work
def pkill():
	os.system('pkill -f client.py; pkill -f master.py; pkill -f worker.py; pkill -f dashboard.py')
	log(DEBUG, "done")
