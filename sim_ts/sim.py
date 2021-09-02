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

def sim_ts(num_req_to_finish=num_req_to_finish, ro=ro, w=20, num_sim=num_sim, write_to_json=False):
	log(DEBUG, "started", w=w)

	return sim_common_w_construct_client(label='ts_w_{}'.format(w),
																			 construct_client=lambda i, env, cl_l: Client_TS('c{}'.format(i), env, num_req_to_finish, w, inter_req_gen_time_rv, serv_time_rv, cl_l),
																			 num_req_to_finish=num_req_to_finish, ro=ro, num_sim=num_sim, write_to_json=write_to_json)

def sim_ET_single_run():
	# num_req_to_finish = 1000 # 10000
	ro = 0.8
	w = 0

	ET, std_T, EW, std_W = sim_ts(num_req_to_finish=num_req_to_finish, ro=ro, w=w, num_sim=1, write_to_json=True)
	log(INFO, "done", ET=ET, std_T=std_T, EW=EW, std_W=std_W)

def sim_ET_vs_ro():
	# num_req_to_finish = 100 # 10000
	# num_sim = 2 # 10
	w = 0 # 20 # 100
	log(DEBUG, "started", w=w)

	sim_w_ro = lambda ro : sim_ts(num_req_to_finish=num_req_to_finish, ro=ro, w=w, num_sim=1, write_to_json=True)
	sim_common_ET_vs_ro('ts_w_{}'.format(w), sim_w_ro)

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	config_m = parse_argv_for_sim(sys.argv[1:])
	set_sim_config(config_m)

	log_sim_config()

	# sim_ET_single_run()
	sim_ET_vs_ro()
