from objs import *

num_cluster = 5
forward_rate, backward_rate = 0.6, 1
state_state_rate_m = {
	1 : {1 : backward_rate, 2 : forward_rate},
	2 : {1 : backward_rate, 3 : forward_rate},
	3 : {2 : backward_rate, 3 : forward_rate}
}
state_cost_m = {1 : 1, 2 : 2, 3 : 3}
inter_probe_time_rv = Exp(mu = 0.2)

def log_global_vars():
	log(DEBUG, "", num_cluster=num_cluster, state_state_rate_m=state_state_rate_m, state_cost_m=state_cost_m, inter_probe_time_rv=inter_probe_time_rv)

def sim_probe_iidClusters_wPodC(d, num_probe=None, num_sim=100, sim_time=1000):
	log(DEBUG, "started", d=d, num_probe=num_probe)

	cum_cost_per_unit_time = 0
	for i in range(num_sim):
		# log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		p = Probe_iidClusters_wPodC(env, num_cluster, state_state_rate_m, state_cost_m, d, inter_probe_time_rv, num_probe)
		# env.run(until=p.wait)
		env.run(until=sim_time)

		cost_per_unit_time = p.get_cost_per_unit_time()
		if cost_per_unit_time is None:
			log(WARNING, "cost_per_unit_time is None")
			continue

		# log(DEBUG, "cost_per_unit_time= {}".format(cost_per_unit_time))
		cum_cost_per_unit_time += cost_per_unit_time

	return cum_cost_per_unit_time / num_sim

def sim_cost_wrt_d():
	d_l, cost_l = [], []
	for d in range(1, num_cluster):
		log(INFO, ">> d= {}".format(d))
		d_l.append(d)

		cost = sim_probe_iidClusters_wPodC(d, num_sim=10, sim_time=1000)
		log(INFO, "cost= {}".format(cost))
		cost_l.append(cost)

	fontsize = 14
	plot.plot(cost_l, d_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=2, ms=2)
	plot.ylabel('Avg cost per unit time', fontsize=fontsize)
	plot.xlabel('d', fontsize=fontsize)
	plot.title('Number of clusters= {}'.format(num_cluster))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_cost_wrt_d.png", bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	# sim_probe_iidClusters_wPodC()
	sim_cost_wrt_d()
