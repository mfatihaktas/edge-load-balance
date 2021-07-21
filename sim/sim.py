import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy
import numpy as np

from rvs import *
from client import *
from cluster import *

# N: # clusters
# n: # workers in each cluster
N, n = 3, 1

# m: # clients
m = 1

d = 1
inter_gen_time_rv = Exp(0.6) # DiscreteRV(p_l=[1], v_l=[1])
serv_time_rv = Exp(1) # DiscreteRV(p_l=[1], v_l=[1])

def log_global_vars():
	log(DEBUG, "", N=N, n=n, m=m, d=d, inter_gen_time_rv=inter_gen_time_rv, serv_time_rv=serv_time_rv)

def sim_PodC(d, inter_probe_num_req, num_req_to_finish, num_sim=1):
	log(DEBUG, "started", d=d, inter_probe_num_req=inter_probe_num_req, num_req_to_finish=num_req_to_finish, num_sim=num_sim)

	cum_cost_per_unit_time = 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		cl_l = [Cluster('cl{}'.format(i), env, num_worker=n) for i in range(N)]
		c_l = [Client('c{}'.format(i), env, d, inter_probe_num_req, num_req_to_finish, inter_gen_time_rv, serv_time_rv, cl_l) for i in range(m)]
		net = Net_wConstantDelay('n', env, [*cl_l, *c_l], delay=0)
		env.run(until=c_l[0].act_recv)

		cum_ET = 0
		t_l = []
		for c in c_l:
			for req in c.req_finished_l:
				t_l.append(req.epoch_arrived_client - req.epoch_departed_client)
		ET = np.mean(t_l)
		log(INFO, "ET= {}".format(ET))
		cum_ET += ET

	log(INFO, 'done')
	return cum_ET / num_sim

def sim_ET_wrt_interProbeNumReqs_d():
	num_probe = None
	num_req_to_finish = 1000
	num_sim = 1 # 3 # 10

	for inter_probe_num_req in [5, 10, 15, 20, 50]:
		log(INFO, ">> inter_probe_num_req= {}".format(inter_probe_num_req))
		d_l, ET_l = [], []
		# for d in [1, 2, 3, *np.linspace(5, N, 4)]:
		for d in range(1, N + 1):
			d = int(d)
			log(INFO, "> d= {}".format(d))
			d_l.append(d)

			ET = sim_PodC(d, inter_probe_num_req, num_req_to_finish, num_sim)
			log(INFO, "ET= {}".format(ET))
			ET_l.append(ET)
		plot.plot(d_l, ET_l, color=next(light_color), label='p= {}'.format(inter_probe_num_req), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$d$', fontsize=fontsize)
	plot.title(r'$N= {}, n= {}, m= {}$'.format(N, n, m) + '\n' \
						 r'$X \sim$ {}, $S \sim {}$'.format(inter_gen_time_rv, serv_time_rv))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_ET_wrt_interProbeNumReqs_N_{}_m_{}.png".format(N, m), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	log_global_vars()

	sim_ET_wrt_interProbeNumReqs_d()
