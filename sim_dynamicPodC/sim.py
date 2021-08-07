import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy
import numpy as np

def sim(m, n, d, rest_time_rv, num_balls_to_gen, num_sim=1):
	log(DEBUG, "started", m=m, n=n, d=d, rest_time_rv=rest_time_rv, num_balls_to_gen=num_balls_to_gen, num_sim=num_sim)

	cum_ET = 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		bin_l = [Bin('bin-{}'.format(i), env, out) for i in range(n)]
		scher = PodCScher(env, d, bin_l)
		bg = BallGen(env, m, rest_time_rv, out=scher)
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
	plot.savefig("plot_ET_wrt_interProbeNumReqs_d_lambda_{}_mu_{}_N_{}_m_{}_Nff_{}.png".format(req_gen_rate, serv_rate, N, m, N_fluctuating_frac), bbox_inches='tight')
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
	plot.savefig("plot_podc_ET_vs_m_ro_{}_N_{}_Nff_{}.png".format(ro, N, N_fluctuating_frac), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	log_global_vars()

	sim_ET_wrt_interProbeNumReqs_d()
	# sim_ET_vs_m()
