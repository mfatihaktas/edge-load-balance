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

def sim_PodC(m, d, inter_probe_num_req, num_req_to_finish, num_sim=1):
	log(DEBUG, "started", d=d, inter_probe_num_req=inter_probe_num_req, num_req_to_finish=num_req_to_finish, num_sim=num_sim)

	inter_req_gen_time_rv = get_inter_req_gen_time_rv(m)

	cum_ET = 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		cl_l = [Cluster('cl{}'.format(i), env, num_worker=n) for i in range(N)]
		c_l = [Client('c{}'.format(i), env, d, inter_probe_num_req, num_req_to_finish, inter_req_gen_time_rv, serv_time_rv, cl_l, initial_cl_id=cl_l[m % N]._id) for i in range(m)]
		if fluctuating_net is False:
			net = Net_wConstantDelay('n', env, [*cl_l, *c_l], net_delay)
		else:
			net = Net_wFluctuatingDelay('n', env, [*cl_l, *c_l], net_delay, net_delay_additional, normal_dur_rv, slow_dur_rv)
			net.reg_as_fluctuating(random.sample(cl_l, num_fluctuating_cl))
		env.run(until=c_l[0].act_recv)

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
	num_req_to_finish = 10000
	num_sim = 3 # 10

	for inter_probe_num_req in [5, 10, 20, 50, 200, 1000, 2000]:
	# for inter_probe_num_req in [2]:
		log(INFO, ">> inter_probe_num_req= {}".format(inter_probe_num_req))
		d_l, ET_l = [], []
		for d in [1, 2, 3, 5, N]:
		# for d in [1, 2, 3, *numpy.arange(5, N + 1, 4)]:
		# for d in range(1, N + 1):
		# for d in [2]:
			d = int(d)
			log(INFO, "> d= {}".format(d))
			d_l.append(d)

			ET = sim_PodC(m, d, inter_probe_num_req, num_req_to_finish, num_sim)
			log(INFO, "ET= {}".format(ET))
			ET_l.append(ET)
			# return
		plot.plot(d_l, ET_l, color=next(light_color), label='p= {}'.format(inter_probe_num_req), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$d$', fontsize=fontsize)
	plot.title(r'$N= {}, n= {}, m= {}$'.format(N, n, m) + '\n' \
						 r'$X \sim {}$, $S \sim {}$'.format(inter_req_gen_time_rv, serv_time_rv))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_ET_wrt_interProbeNumReqs_d_lambda_{}_mu_{}_N_{}_m_{}_fluctuatingNet_{}.png".format(req_gen_rate, serv_rate, N, m, fluctuating_net), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

def sim_ET_vs_m():
	num_req_to_finish = 10000 # 100
	num_sim = 2 # 10

	d = 2
	inter_probe_num_req = 50

	m_l, ET_l = [], []
	for m in [1, 2, N, 2*N, 3*N]:
	# for m in [2]:
		m_l.append(m)

		ET = sim_PodC(m, d, inter_probe_num_req, num_req_to_finish, num_sim)
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
	plot.savefig("plot_podc_ET_vs_m_ro_{}_N_{}_fluctuatingNet_{}.png".format(ro, N, fluctuating_net), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	log_global_vars()

	sim_ET_wrt_interProbeNumReqs_d()
	# sim_ET_vs_m()
