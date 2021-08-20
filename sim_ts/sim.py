import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir + '/sim_common')
sys.path.append(parent_dir)

import simpy, json
import numpy as np

from rvs import *
from client import *
from cluster import *

from sim_config import *

def sim_thompsonSampling(ro, num_req_to_finish, num_sim=1):
	log(DEBUG, "started", ro=ro, num_req_to_finish=num_req_to_finish, num_sim=num_sim)

	inter_req_gen_time_rv = get_inter_req_gen_time_rv(ro, m)

	cum_ET = 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		cl_l = [Cluster('cl{}'.format(i), env, num_worker=n) for i in range(N)]
		c_l = [Client('c{}'.format(i), env, num_req_to_finish, inter_req_gen_time_rv, serv_time_rv, cl_l) for i in range(m)]
		net = Net_FCFS('n', env, [*cl_l, *c_l], net_speed)
		if N_fluctuating_frac:
			net.reg_as_fluctuating(random.sample(cl_l, int(N * N_fluctuating_frac)), net_slowdown, normal_dur_rv, slow_dur_rv)
		env.run(until=c_l[0].act_recv)

		t_l, w_l = [], []
		for c in c_l:
			for req in c.req_finished_l:
				t = req.epoch_arrived_client - req.epoch_departed_client
				t_l.append(t)
				w_l.append(t - req.serv_time)

		write_to_file(data=json.dumps(t_l), fname=get_filename_json(header='sim_ts_resptime'))
		write_to_file(data=json.dumps(w_l), fname=get_filename_json(header='sim_ts_waittime'))

		ET = np.mean(t_l)
		log(INFO, "ET= {}".format(ET))
		cum_ET += ET

	log(INFO, "done")
	return cum_ET / num_sim

def sim_ET_for_single_m():
	num_req_to_finish = 10000 # 100

	ET = sim_thompsonSampling(m, num_req_to_finish, num_sim=1)
	log(DEBUG, "done", ET=ET)

def sim_ET_vs_ro():
	num_req_to_finish = 10000
	num_sim = 2 # 10

	ro_l, ET_l = [], []
	for ro in [0.2, 0.5, 0.8]:
		log(INFO, "> ro= {}".format(ro))
		ro_l.append(ro)

		ET = sim_thompsonSampling(ro, num_req_to_finish, num_sim)
		log(INFO, "ET= {}".format(ET))
		ET_l.append(ET)

	plot.plot(ro_l, ET_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$\rho$', fontsize=fontsize)
	plot.title(get_plot_title())
	plot.gcf().set_size_inches(6, 4)
	plot.savefig(get_filename_png("plot_ts_ET_vs_ro"), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	log_sim_config()

	sim_ET_vs_ro()
	# sim_ET_for_single_m()
