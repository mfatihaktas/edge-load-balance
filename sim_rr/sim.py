import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir + '/sim_common')
sys.path.append(parent_dir)

import simpy, json

from rvs import *
from client import *
from cluster import *

from sim_config import *
from sim_utils import *

def sim_rr(num_req_to_finish=num_req_to_finish, ro=ro, num_sim=1, write_to_json=False):
	log(DEBUG, "started", num_req_to_finish=num_req_to_finish, ro=ro, num_sim=num_sim, write_to_json=write_to_json)

	inter_req_gen_time_rv = get_inter_req_gen_time_rv(ro, m)

	cum_ET, cum_std_T, cum_EW, cum_std_W = 0, 0, 0, 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		cl_l = get_cl_l(env)
		c_l = [Client_RR('c{}'.format(i), env, num_req_to_finish, inter_req_gen_time_rv, serv_time_rv, cl_l) for i in range(m)]
		net = Net('n', env, [*cl_l, *c_l])
		env.run(until=c_l[0].act_recv)

		stats_m = get_stats_m_from_sim_data(cl_l, c_l, header='rr' if write_to_json else None, ro=ro)

		ET, std_T = stats_m['ET'], stats_m['std_T']
		EW, std_W = stats_m['EW'], stats_m['std_W']
		log(INFO, "", ET=ET, std_T=std_T, EW=EW, std_W=std_W)
		cum_ET += ET
		cum_std_T += std_T
		cum_EW += EW
		cum_std_W += std_W

	log(INFO, "done")
	return cum_ET / num_sim, cum_std_T / num_sim, cum_EW / num_sim, cum_std_W / num_sim

def sim_ET_for_single_m():
	# num_req_to_finish = 10000

	d, p = 2, 10
	ET, std_T, EW, std_W = sim_rr(num_req_to_finish=num_req_to_finish, write_to_json=True)
	log(INFO, "done", ET=ET, std_T=std_T, EW=EW, std_W=std_W)

def sim_ET_vs_ro():
	num_req_to_finish = 100 # 10000
	# num_sim = 2 # 10
	w = 0 # 20 # 100
	log(DEBUG, "started", num_req_to_finish=num_req_to_finish, num_sim=num_sim, w=w)

	sim_w_ro = lambda ro : sim_rr(num_req_to_finish=num_req_to_finish, num_sim=num_sim, ro=ro, write_to_json=True)
	sim_common_ET_vs_ro('rr', sim_w_ro)

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	config_m = parse_argv_for_sim(sys.argv[1:])
	set_sim_config(config_m)

	log_sim_config()

	# sim_ET_for_single_m()
	sim_ET_vs_ro()
