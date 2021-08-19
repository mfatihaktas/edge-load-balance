import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_dir + '/sim_common')

from plot_utils import *
from debug_utils import *
from sim_config import *

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

def plot_cdf_T_W__podc_vs_ts():
	d, p = 2, 5
	subfolder_podc, subfolder_ts = 'sim_podc', 'sim_ts'
	T_podc_l = read_json_from_file(fname=get_filename_json(header='{}/sim_podc_resptime_d_{}_p_{}'.format(subfolder_podc, d, p)))
	W_podc_l = read_json_from_file(fname=get_filename_json(header='{}/sim_podc_waittime_d_{}_p_{}'.format(subfolder_podc, d, p)))
	T_ts_l = read_json_from_file(fname=get_filename_json(header='{}/sim_ts_resptime'.format(subfolder_ts)))
	W_ts_l = read_json_from_file(fname=get_filename_json(header='{}/sim_ts_waittime'.format(subfolder_ts)))

	fontsize = 14
	fig, axs = plot.subplots(1, 2)
	figsize = (2*6, 4)

	## CDF of W
	ax = axs[0]
	plot.sca(ax)
	add_cdf(W_podc_l, ax, 'PodC', next(nice_color)) # drawline_x_l=[1000]
	add_cdf(W_ts_l, ax, 'TS', next(nice_color)) # drawline_x_l=[1000]
	plot.xscale('log')
	# plot.xticks(rotation=70)
	plot.ylabel('Pr{W < x}', fontsize=fontsize)
	plot.xlabel('x', fontsize=fontsize)
	plot.legend(fontsize=fontsize)

	## CDF of T
	ax = axs[1]
	plot.sca(ax)
	add_cdf(T_podc_l, ax, 'PodC', next(nice_color))
	add_cdf(T_ts_l, ax, 'TS', next(nice_color))
	plot.xscale('log')
	plot.ylabel('Pr{T < x}', fontsize=fontsize)
	plot.xlabel('x', fontsize=fontsize)
	plot.legend(fontsize=fontsize)

	fig.set_size_inches(figsize[0], figsize[1] )
	plot.subplots_adjust(hspace=0.45, wspace=0.45)

	st = plot.suptitle(r'$N= {}, n= {}, m= {}, \rho= {}, S \sim {}$'.format(N, n, m, ro, serv_time_rv), fontsize=14)
	plot.savefig(get_filename_png("plot_cdf_T_W__podc_vs_ts"), bbox_extra_artists=(st,), bbox_inches='tight')
	fig.clear()

	log(DEBUG, "done.")

if __name__ == '__main__':
	plot_cdf_T_W__podc_vs_ts()
