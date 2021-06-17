from plot_utils import *
from debug_utils import *

def plot_client(c):
	fontsize = 14
	## T over time
	t0 = c.req_finished_l[0].epoch_arrived_client
	t_l, T_l = [], []
	for req in c.req_finished_l:
		t_l.append(req.epoch_arrived_client - t0)
		T_l.append(1000*(req.epoch_arrived_client - req.epoch_departed_client))
	plot.plot(t_l, T_l, color=next(nice_color), marker='_', linestyle='None', mew=3, ms=5)
	plot.ylabel('T (msec)', fontsize=fontsize)
	plot.xlabel('t', fontsize=fontsize)
	plot.legend(fontsize=fontsize)
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_{}_T_over_t.png".format(c._id), bbox_inches='tight')
	plot.gcf().clear()

	## CDF of T
	add_cdf(T_l, plot.gca(), '', next(nice_color)) # drawline_x_l=[1000]
	plot.xscale('log')
	plot.xticks(rotation=70)
	plot.ylabel('Pr{T < x}', fontsize=fontsize)
	plot.xlabel('x (msec)', fontsize=fontsize)
	plot.legend(fontsize=fontsize)
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_{}_cdf_T.png".format(c._id), bbox_inches='tight')
	plot.gcf().clear()

	## CDF of inter result times
	add_cdf(c.inter_result_time_l, plot.gca(), '', next(nice_color)) # drawline_x_l=[1000*c.inter_job_gen_time_rv.mean()]
	plot.xscale('log')
	plot.xticks(rotation=70)
	plot.ylabel('Pr{Inter result time < x}', fontsize=fontsize)
	plot.xlabel('x (msec)', fontsize=fontsize)
	plot.legend(fontsize=fontsize)
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_{}_cdf_interResultTime.png".format(c._id), bbox_inches='tight')

	log(DEBUG, "done.")

def plot_master(m):
	log(DEBUG, "", num_dropped_msgs=m.msg_q.num_dropped)

def plot_worker(w):
	fontsize = 14
	## Q-length over time
	t0 = w.epoch__num_req_l[0]
	t_l, nreq_l = [], []
	for epoch, nreq in w.epoch__num_req_l:
		t_l.append(epoch - t0)
		nreq_l.append(nreq)
	plot.plot(t_l, nreq_l, color=next(nice_color), marker='_', linestyle='None', mew=3, ms=5)
	plot.ylabel('Number of requests', fontsize=fontsize)
	plot.xlabel('t', fontsize=fontsize)
	plot.legend(fontsize=fontsize)
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_{}_n_over_t.png".format(w._id), bbox_inches='tight')
	plot.gcf().clear()
