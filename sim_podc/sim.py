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

def sim_podc(d, interProbeNumReq_controller, num_req_to_finish, num_sim=1, write_to_json=False, ro=ro):
	log(DEBUG, "started", d=d, interProbeNumReq_controller=interProbeNumReq_controller, ro=ro, num_req_to_finish=num_req_to_finish, num_sim=num_sim, write_to_json=write_to_json)

	inter_req_gen_time_rv = get_inter_req_gen_time_rv(ro, m)

	cum_ET, cum_EW = 0, 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		cl_l = get_cl_l(env)
		c_l = [Client_PodC('c{}'.format(i), env, d, interProbeNumReq_controller, num_req_to_finish, inter_req_gen_time_rv, serv_time_rv, cl_l, initial_cl_id=cl_l[m % N]._id) for i in range(m)]
		net = Net('n', env, [*cl_l, *c_l])
		env.run(until=c_l[0].act_recv)

		stats_m = get_stats_m_from_sim_data(c_l, header='podc_d_{}_p_{}'.format(d, interProbeNumReq_controller.num) if write_to_json else None)

		ET, EW = stats_m['ET'], stats_m['EW']
		log(INFO, "", ET=ET, EW=EW)
		cum_ET += ET
		cum_EW += EW

	log(INFO, 'done')
	return cum_ET / num_sim, cum_EW / num_sim

def sim_ET_wrt_p_d():
	num_req_to_finish = 10000
	num_sim = 2 # 10

	## InterProbeNumReq_controller_learningWConstInc
	# '''
	log(INFO, "InterProbeNumReq_controller_learningWConstInc")
	d_l, ET_l = [], []
	for d in [1, 2, 5, N]:
	# for d in [1, 2, 3, 5, N]:
		log(INFO, "> d= {}".format(d))
		d_l.append(d)

		p_controller = InterProbeNumReq_controller_learningWConstInc(num=5, inc=1)
		ET, EW = sim_podc(d, p_controller, num_req_to_finish, num_sim)
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
	# '''

	## InterProbeNumReq_controller_constant
	log(INFO, "InterProbeNumReq_controller_constant")
	for p in [5, 50, 1000]:
	# for p in [5, 10, 20, 50, 200, 1000, 2000]:
	# for p in [2]:
		log(INFO, ">> p= {}".format(p))

		d_l, ET_l = [], []
		for d in [1, 2, 3, N]:
		# for d in [1, 2, 3, 5, N]:
		# for d in [1, 2, 3, *numpy.arange(5, N + 1, 4)]:
		# for d in range(1, N + 1):
		# for d in [2]:
			d = int(d)
			log(INFO, "> d= {}".format(d))
			d_l.append(d)

			ET, EW = sim_podc(d, InterProbeNumReq_controller_constant(p), num_req_to_finish, num_sim)
			log(INFO, "ET= {}".format(ET))
			ET_l.append(ET)
		plot.plot(d_l, ET_l, color=next(light_color), label='p= {}'.format(p), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$d$', fontsize=fontsize)
	plot.title(get_plot_title())
	plot.gcf().set_size_inches(6, 4)
	plot.savefig(get_filename_png("plot_ET_wrt_p_d"), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

def sim_ET_single_run():
	num_req_to_finish = 10000 # 100

	d, p = 2, 10
	ET, EW = sim_podc(d, InterProbeNumReq_controller_constant(p), num_req_to_finish, num_sim=1, write_to_json=True)
	log(DEBUG, "done", ET=ET)

def sim_ET_vs_ro():
	num_req_to_finish = 10 # 10000 # 100
	num_sim = 2 # 10

	d = 2
	p = 10

	ro_l, ET_l, EW_l = [], [], []
	for ro in [0.2, 0.5, 0.65, 0.8, 0.9]:
		log(INFO, "> ro= {}".format(ro))
		ro_l.append(ro)

		ET, EW = sim_podc(d, InterProbeNumReq_controller_constant(p), num_req_to_finish, num_sim, ro=ro, write_to_json=True)
		log(INFO, "ET= {}".format(ET))
		ET_l.append(ET)
		EW_l.append(EW)

	write_to_file(data=json.dumps(list(zip(ro_l, ET_l))), fname=get_filename_json(header='ro_ET_l_podc_d_{}_p_{}'.format(d, p)))
	write_to_file(data=json.dumps(list(zip(ro_l, EW_l))), fname=get_filename_json(header='ro_EW_l_podc_d_{}_p_{}'.format(d, p)))

	plot.plot(ro_l, ET_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$\rho$', fontsize=fontsize)
	plot.title(r'$d= {}, p= {}$'.format(d, p) + ', ' + get_plot_title())
	plot.gcf().set_size_inches(6, 4)
	plot.savefig(get_filename_png("plot_podc_ET_vs_ro"), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	log_sim_config()

	# sim_ET_wrt_p_d()
	# sim_ET_single_run()
	sim_ET_vs_ro()
