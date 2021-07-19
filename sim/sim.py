import numpy as np

from objs import *
from sim_utils import *

num_cluster = 20
forward_rate, backward_rate = 0.9, 1 # 1, 1 # 0.6, 1
# state_state_rate_m = {
#		1 : {1 : backward_rate, 2 : forward_rate},
#		2 : {1 : backward_rate, 3 : forward_rate},
#		3 : {2 : backward_rate, 3 : forward_rate}
# }
# state_state_rate_m = {s : {s - 1 : backward_rate, s + 1 : forward_rate} for s in range(20)}
state_state_rate_m = {}
num_state = 20
for s in range(num_state):
	if s == 0:
		m = {s : backward_rate, s + 1 : forward_rate}
	elif s == num_state - 1:
		m = {s - 1 : backward_rate, s : forward_rate}
	else:
		m = {s - 1 : backward_rate, s + 1 : forward_rate}
	state_state_rate_m[s] = m

state_cost_m = {s : s for s in state_state_rate_m}
inter_probe_time_rv = DiscreteRV(p_l=[1], v_l=[1]) # Exp(mu = 0.2)

def log_global_vars():
	log(DEBUG, "", num_cluster=num_cluster, state_state_rate_m=state_state_rate_m, state_cost_m=state_cost_m, inter_probe_time_rv=inter_probe_time_rv)

def sim_probe_iidClusters_wPodC(d, x, num_probe=None, num_sim=100, sim_time=1000):
	# log(INFO, "started", d=d, inter_probe_time_rv=inter_probe_time_rv, num_probe=num_probe, num_sim=num_sim, sim_time=sim_time)
	inter_probe_time_rv = DiscreteRV(p_l=[1], v_l=[x], norm_factor=1000)

	cum_cost_per_unit_time = 0
	for i in range(num_sim):
		# log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		p = Probe_iidClusters_wPodC(env, num_cluster, state_state_rate_m, state_cost_m, d, inter_probe_time_rv, num_probe)
		# env.run(until=p.wait)
		env.run(until=sim_time)

		# if i == 0:
		# 	plot_cost_over_time(p, d, x, forward_rate, backward_rate)

		cost_per_unit_time = p.get_cost_per_unit_time()
		# log(INFO, '', cost_per_unit_time=cost_per_unit_time)
		if cost_per_unit_time is None:
			log(WARNING, "cost_per_unit_time is None")
			continue

		# log(DEBUG, "cost_per_unit_time= {}".format(cost_per_unit_time))
		cum_cost_per_unit_time += cost_per_unit_time

	# log(INFO, 'done')
	return cum_cost_per_unit_time / num_sim

def sim_cost_wrt_d():
	num_probe = None
	num_sim = 10
	sim_time = 1000

	d_l, cost_l = [], []
	# for d in range(1, num_cluster + 1):
	for d in [1, 2, 3, *np.linspace(5, num_cluster, 4)]:
		d = int(d)
		log(INFO, ">> d= {}".format(d))
		d_l.append(d)

		cost = sim_probe_iidClusters_wPodC(d, 1, num_probe, num_sim, sim_time)
		log(INFO, "cost= {}".format(cost))
		cost_l.append(cost)

	fontsize = 14
	plot.plot(d_l, cost_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)
	plot.ylabel(r'$E[C]$' + ' per unit time', fontsize=fontsize)
	plot.xlabel(r'$d$', fontsize=fontsize)
	plot.title(r'$N= {}$'.format(num_cluster))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_cost_wrt_d.png", bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

def sim_cost_wrt_interProbeTime_d():
	num_probe = None
	num_sim = 1 # 3 # 10
	sim_time = 50 # 0 # 1000 # 2000

	for x in [1, 2, 5, 10, 20, 50]:
		log(INFO, ">> x= {}".format(x))
		d_l, cost_l = [], []
		for d in [1, 2, 3, *np.linspace(5, num_cluster, 4)]:
			d = int(d)
			log(INFO, "> d= {}".format(d))
			d_l.append(d)

			cost = sim_probe_iidClusters_wPodC(d, x, num_probe, num_sim, sim_time)
			log(INFO, "cost= {}".format(cost))
			cost_l.append(cost)
		plot.plot(d_l, cost_l, color=next(nice_color), label='x= {}'.format(x), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[C]$' + ' per unit time', fontsize=fontsize)
	plot.xlabel(r'$d$', fontsize=fontsize)
	plot.title(r'$N= {}, \lambda= {}, \mu= {}$'.format(num_cluster, forward_rate, backward_rate))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_cost_wrt_interProbeTime_d_lambda_{}_mu_{}.png".format(forward_rate, backward_rate), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	# sim_cost_wrt_d()
	sim_cost_wrt_interProbeTime_d()
