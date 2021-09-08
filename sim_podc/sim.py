import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir + '/sim_common')
sys.path.append(parent_dir)

import simpy, json
import numpy as np

import client

import sim_config
import sim_utils
from plot_utils import *
from file_utils import *
from debug_utils import *

def sim_podc(d, interProbeNumReq_controller, num_req_to_finish, ro, num_sim, write_to_json=False):
	log(DEBUG, "started", d=d, interProbeNumReq_controller=interProbeNumReq_controller)

	return sim_utils.sim_common_w_construct_client(
					 label='podc_d_{}_p_{}'.format(d, interProbeNumReq_controller.num),
					 construct_client=lambda i, env, cl_l, inter_req_gen_time_rv: client.Client_PodC('c{}'.format(i), env, d, interProbeNumReq_controller, sim_config.num_req_to_finish, inter_req_gen_time_rv, sim_config.serv_time_rv, cl_l, initial_cl_id=cl_l[i % sim_config.N]._id),
					 num_req_to_finish=num_req_to_finish, ro=ro, num_sim=num_sim, write_to_json=write_to_json)

def sim_ET_vs_d_p():
	# num_req_to_finish = 10000
	# num_sim = 2 # 10

	## InterProbeNumReq_controller_learningWConstInc
	'''
	log(INFO, "InterProbeNumReq_controller_learningWConstInc")
	d_l, ET_l = [], []
	for d in [1, 2, 5, N]:
	# for d in [1, 2, 3, 5, N]:
		log(INFO, "> d= {}".format(d))
		d_l.append(d)

		p_controller = InterProbeNumReq_controller_learningWConstInc(num=5, inc=1)
		ET, std_T, EW, std_W = sim_podc(d, p_controller, num_req_to_finish, num_sim)
		log(INFO, "ET= {}".format(ET))
		ET_l.append(ET)

		plot.plot(list(range(len(p_controller.num_l))), p_controller.num_l, color=next(nice_color), label='d= '.format(d), marker='o', linestyle='dotted', lw=2, mew=3, ms=5)
		fontsize = 14
		plot.legend(fontsize=fontsize)
		plot.ylabel('Time', fontsize=fontsize)
		plot.xlabel('Inter-probe # requests', fontsize=fontsize)
		plot.title(get_plot_title() + ', Mean= {}'.format(np.mean(p_controller.num_l)))
		plot.gcf().set_size_inches(12, 4)
		plot.savefig("plot_p_over_time_d_{}.png".format(d), bbox_inches='tight')
		plot.gcf().clear()

	plot.plot(d_l, ET_l, color=next(dark_color), label='learning', marker='x', linestyle='dotted', lw=2, mew=3, ms=5)
	'''

	## InterProbeNumReq_controller_constant
	log(INFO, "InterProbeNumReq_controller_constant")
	for p in [1, 200]:
	# for p in [5, 10, 50, 1000]:
	# for p in [5, 10, 20, 50, 200, 1000, 2000]:
	# for p in [2]:
		log(INFO, ">> p= {}".format(p))

		d_l, ET_l, std_T_l = [], [], []
		for d in [1, 2, 3, 4, sim_config.N]:
		# for d in [1, 2, 3, 5, N]:
		# for d in [1, 2, 3, *numpy.arange(5, N + 1, 4)]:
		# for d in range(1, N + 1):
		# for d in [2]:
			d = int(d)
			log(INFO, "> d= {}".format(d))
			d_l.append(d)

			ET, std_T, EW, std_W = sim_podc(d, client.InterProbeNumReq_controller_constant(p), sim_config.num_req_to_finish, sim_config.ro, sim_config.num_sim)
			log(INFO, "", ET=ET, std_T=std_T, EW=EW, std_W=std_W)
			ET_l.append(ET)
			std_T_l.append(std_T)
		# plot.errorbar(d_l, ET_l, yerr=std_T_l, color=next(light_color), label='p= {}'.format(p), marker='x', linestyle='solid', lw=2, mew=3, ms=5)
		plot.plot(d_l, ET_l, color=next(light_color), label='p= {}'.format(p), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

		write_to_file(data=json.dumps(list(zip(d_l, ET_l))), fname=sim_config.get_filename_json(header='d_ET_l_podc_p_{}'.format(p), ro_arg=sim_config.ro))

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$d$', fontsize=fontsize)
	plot.title(sim_config.get_plot_title())
	plot.gcf().set_size_inches(6, 4)
	plot.savefig(sim_config.get_filename_png("plot_ET_vs_d_p"), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

def sim_ET_single_run():
	# num_req_to_finish = 10000 # 100

	d, p = 2, 10
	ET, std_T, EW, std_W = sim_podc(d, InterProbeNumReq_controller_constant(p), sim_config.num_req_to_finish, sim_config.ro, num_sim=1, write_to_json=True)
	log(DEBUG, "done", ET=ET, std_T=std_T, EW=EW, std_W=std_W)

def sim_ET_vs_ro():
	# num_req_to_finish = 100 # 10000
	# num_sim = 2 # 10
	d, p = 2, 10
	log(DEBUG, "started", d=d, p=p)

	sim_w_ro = lambda ro : sim_podc(d=d, interProbeNumReq_controller=client.InterProbeNumReq_controller_constant(p), num_req_to_finish=sim_config.num_req_to_finish, ro=ro, num_sim=sim_config.num_sim, write_to_json=True)
	sim_utils.sim_common_ET_vs_ro('podc_d_{}_p_{}'.format(d, p), sim_w_ro)

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	config_m = sim_utils.parse_argv_for_sim(sys.argv[1:])
	sim_config.set_sim_config(config_m)

	sim_config.log_sim_config()

	sim_ET_vs_d_p()
	# sim_ET_single_run()
	# sim_ET_vs_ro()
