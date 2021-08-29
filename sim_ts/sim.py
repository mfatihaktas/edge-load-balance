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
from sim_utils import *

def sim_ts(num_req_to_finish, ro=ro, w=20, num_sim=1, write_to_json=False):
	log(DEBUG, "started", ro=ro, w=w, num_req_to_finish=num_req_to_finish, num_sim=num_sim)

	inter_req_gen_time_rv = get_inter_req_gen_time_rv(ro, m)

	cum_ET, cum_EW = 0, 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		cl_l = get_cl_l(env)
		c_l = [Client_TS('c{}'.format(i), env, num_req_to_finish, w, inter_req_gen_time_rv, serv_time_rv, cl_l) for i in range(m)]
		net = Net('n', env, [*cl_l, *c_l])
		env.run(until=c_l[0].act_recv)

		stats_m = get_stats_m_from_sim_data(cl_l, c_l, header='ts_w_{}'.format(w) if write_to_json else None, ro=ro)

		ET, EW = stats_m['ET'], stats_m['EW']
		log(INFO, "", ET=ET, EW=EW)
		cum_ET += ET
		cum_EW += EW

	log(INFO, "done")
	return cum_ET / num_sim, cum_EW / num_sim

def sim_ET_single_run():
	num_req_to_finish = 10000 # 100

	ET, EW = sim_ts(num_req_to_finish=num_req_to_finish, num_sim=1, write_to_json=True)
	log(DEBUG, "done", ET=ET, EW=EW)

def sim_ET_vs_ro():
	num_req_to_finish = 10000
	w = 20 # 100
	num_sim = 2 # 10

	ro_l, ET_l, EW_l = [], [], []
	for ro in [0.2, 0.5, 0.65, 0.8, 0.9]:
		log(INFO, "> ro= {}".format(ro))
		ro_l.append(ro)

		ET, EW = sim_ts(num_req_to_finish=num_req_to_finish, ro=ro, w=w, num_sim=num_sim, write_to_json=True)
		log(INFO, "", ET=ET, EW=EW)
		ET_l.append(ET)
		EW_l.append(EW)

	write_to_file(data=json.dumps(list(zip(ro_l, ET_l))), fname=get_filename_json(header='ro_ET_l_ts_w_{}'.format(w), ro=ro))
	write_to_file(data=json.dumps(list(zip(ro_l, EW_l))), fname=get_filename_json(header='ro_EW_l_ts_w_{}'.format(w), ro=ro))

	plot.plot(ro_l, ET_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)
	plot.plot(ro_l, EW_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

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

	# sim_ET_single_run()
	sim_ET_vs_ro()
