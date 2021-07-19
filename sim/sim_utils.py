import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from plot_utils import *
from debug_utils import *

def plot_cost_over_time(sim_obj, d, x, forward_rate, backward_rate):
	log(DEBUG, "started", sim_obj=sim_obj, d=d, x=x, forward_rate=forward_rate, backward_rate=backward_rate)
	epoch_cost_l = sim_obj.epoch_cost_l

	x_l, y_l = [], []
	for i in range(len(epoch_cost_l) - 1):
		epoch, cost = epoch_cost_l[i]
		x_l.append(epoch)
		y_l.append(cost)
		x_l.append(epoch_cost_l[i+1][0])
		y_l.append(cost)

	fontsize = 14
	plot.plot(x_l, y_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)
	plot.ylabel(r'$E[C]$' + ' per unit time', fontsize=fontsize)
	plot.xlabel('Time', fontsize=fontsize)
	plot.title(r'$N= {}, \lambda= {}, \mu= {}$'.format(sim_obj.num_cluster, forward_rate, backward_rate))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_cost_over_time_d_{}_x_{}_lambda_{}_mu_{}.png".format(d, x, forward_rate, backward_rate), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")
