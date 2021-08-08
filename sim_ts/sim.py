import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir + '/sim_common')
sys.path.append(parent_dir)

import simpy
import numpy as np

from rvs import *
from client import *
from cluster import *

from sim_config import *

def sim_thompsonSampling(m, num_req_to_finish, num_sim=1):
	log(DEBUG, "started", num_req_to_finish=num_req_to_finish, num_sim=num_sim)

	inter_req_gen_time_rv = get_inter_req_gen_time_rv(m)

	cum_ET = 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		cl_l = [Cluster('cl{}'.format(i), env, num_worker=n) for i in range(N)]
		c_l = [Client('c{}'.format(i), env, num_req_to_finish, inter_req_gen_time_rv, serv_time_rv, cl_l) for i in range(m)]
		if N_fluctuating_frac:
			net = Net_wFluctuatingDelay('n', env, [*cl_l, *c_l], net_delay, net_delay_additional, normal_dur_rv, slow_dur_rv)
			net.reg_as_fluctuating(random.sample(cl_l, int(N * N_fluctuating_frac)))
		else:
			net = Net_wConstantDelay('n', env, [*cl_l, *c_l], net_delay)
		env.run(until=c_l[0].act_recv)

		t_l = []
		for c in c_l:
			for req in c.req_finished_l:
				t_l.append(req.epoch_arrived_client - req.epoch_departed_client)
		ET = np.mean(t_l)
		log(INFO, "ET= {}".format(ET))
		cum_ET += ET

	log(INFO, "done")
	return cum_ET / num_sim

def sim_ET_vs_m():
	num_req_to_finish = 5000 # 100
	num_sim = 2 # 10

	m_l, ET_l = [], []
	for m in [1, 2, N, 2*N, 3*N]:
	# for m in [2]:
		m_l.append(m)

		ET = sim_thompsonSampling(m, num_req_to_finish, num_sim)
		log(INFO, "ET= {}".format(ET))
		ET_l.append(ET)

	plot.plot(m_l, ET_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$m$', fontsize=fontsize)
	plot.title(r'$N= {}, n= {}$'.format(N, n) + ', ' \
						 r'$\rho= {}$, $S \sim {}$'.format(ro, serv_time_rv))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_ts_ET_wrt_m_ro_{}_N_{}_Nff_{}.png".format(ro, N, N_fluctuating_frac), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	log_sim_config()

	sim_ET_vs_m()