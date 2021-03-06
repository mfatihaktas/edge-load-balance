import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy

from objs import *
from rvs import *

def sim_EI(m, n, d, ball_restime_rv, num_balls_to_gen, frac_fluctuating=0, slow_dur_rv=None, normal_dur_rv=None, num_sim=1):
	log(DEBUG, "started", m=m, n=n, d=d, ball_restime_rv=ball_restime_rv, num_balls_to_gen=num_balls_to_gen, frac_fluctuating=frac_fluctuating, slow_dur_rv=slow_dur_rv, normal_dur_rv=normal_dur_rv, num_sim=num_sim)

	cum_EI = 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		bg = BallGen(env, m, ball_restime_rv, num_balls_to_gen)
		bc = BinCluster(env, n, d, ball_restime_rv, bg, frac_fluctuating, slow_dur_rv, normal_dur_rv)
		env.run(until=bg.act)

		check(len(bc.epoch_I_l) > 1, "BinCluster.epoch_I_l should have at least two elements")
		sim_dur = bc.epoch_I_l[-1][0] - bc.epoch_I_l[0][0]
		EI = 0
		for i in range(1, len(bc.epoch_I_l)):
			_e, _I = bc.epoch_I_l[i-1]
			e, I = bc.epoch_I_l[i]
			EI += _I * (e - _e)  / sim_dur
		log(INFO, "EI= {}".format(EI))
		cum_EI += EI

	log(INFO, "done")
	return cum_EI / num_sim

def plot_EI_vs_d_restime(n):
	log(INFO, "started", n=n)

	m = 10 * n
	num_balls_to_gen = 100 * m
	num_sim = 2

	frac_fluctuating = 0.2
	slow_dur_rv = DiscreteRV(p_l=[1], v_l=[10])
	normal_dur_rv = DiscreteRV(p_l=[1], v_l=[30])

	# for t in [1, 2, 3, 4]:
	# for t in [1, 2, 3, 10]:
	for t in [1, 10, 50, 100]:
		log(INFO, ">> t= {}".format(t))
		ball_restime_rv = DiscreteRV(p_l=[1], v_l=[t])

		d_l, EI_l = [], []
		for d in [1, 2, 3, n]:
			log(INFO, "> d= {}".format(d))
			d_l.append(d)

			EI = sim_EI(m, n, d, ball_restime_rv, num_balls_to_gen, frac_fluctuating, slow_dur_rv, normal_dur_rv, num_sim)
			log(INFO, "EI= {}".format(EI))
			EI_l.append(EI)
			# return
		plot.plot(d_l, EI_l, color=next(dark_color), label='t= {}'.format(t), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[I]$', fontsize=fontsize)
	plot.xlabel(r'$d$', fontsize=fontsize)
	plot.title(r'$m= {}$, $n= {}$, $f= {}$'.format(m, n, frac_fluctuating) + '\n' \
						 r'$T_s \sim${}, $T_n \sim${}'.format(slow_dur_rv, normal_dur_rv))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_EI_vs_d_restime_n_{}_f_{}.png".format(n, frac_fluctuating), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	plot_EI_vs_d_restime(n=100)
