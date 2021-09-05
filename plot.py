import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_dir + '/sim_common')

import threading

from plot_utils import *
from file_utils import *
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

	log(DEBUG, "done")

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

SUBFOLDER_PODC = 'sim_podc'
SUBFOLDER_TS = 'sim_ts'
SUBFOLDER_RR = 'sim_rr'
SUBFOLDER_UCB = 'sim_ucb'
d, p = 2, 10
w = 0 # 20 # 100

def plot_cdf_T_W__podc_vs_ts(ro, hetero_clusters, N_fluctuating_frac, serv_time_rv):
	log(INFO, "started", ro=ro, hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv)

	T_podc_l = read_json_from_file(fname=get_filename_json('{}/T_l_podc_d_{}_p_{}'.format(SUBFOLDER_PODC, d, p), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	W_podc_l = read_json_from_file(fname=get_filename_json('{}/W_l_podc_d_{}_p_{}'.format(SUBFOLDER_PODC, d, p), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	T_ts_w_0_l = read_json_from_file(fname=get_filename_json('{}/T_l_ts_w_0'.format(SUBFOLDER_TS), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	W_ts_w_0_l = read_json_from_file(fname=get_filename_json('{}/W_l_ts_w_0'.format(SUBFOLDER_TS), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	T_ts_w_20_l = read_json_from_file(fname=get_filename_json('{}/T_l_ts_w_20'.format(SUBFOLDER_TS), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	W_ts_w_20_l = read_json_from_file(fname=get_filename_json('{}/W_l_ts_w_20'.format(SUBFOLDER_TS), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	T_rr_l = read_json_from_file(fname=get_filename_json('{}/T_l_rr'.format(SUBFOLDER_RR), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	W_rr_l = read_json_from_file(fname=get_filename_json('{}/W_l_rr'.format(SUBFOLDER_RR), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	T_ucb_w_20_l = read_json_from_file(fname=get_filename_json('{}/T_l_ucb_w_20'.format(SUBFOLDER_UCB), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	W_ucb_w_20_l = read_json_from_file(fname=get_filename_json('{}/W_l_ucb_w_20'.format(SUBFOLDER_UCB), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))

	fontsize = 14
	fig, axs = plot.subplots(1, 2)
	figsize = (2*10, 5)

	## CDF of W
	ax = axs[0]
	plot.sca(ax)
	add_cdf(W_podc_l, ax, 'PodC', next(light_color)) # drawline_x_l=[1000]
	add_cdf(W_ts_w_0_l, ax, 'TS, w=0', next(light_color))
	add_cdf(W_ts_w_20_l, ax, 'TS, w=20', next(light_color))
	add_cdf(W_rr_l, ax, 'RR', next(light_color))
	add_cdf(W_ucb_w_20_l, ax, 'UCB', next(light_color))
	plot.xscale('log')
	# plot.xticks(rotation=70)
	plot.ylabel('Pr{W < x}', fontsize=fontsize)
	plot.xlabel('x', fontsize=fontsize)
	legend1 = plot.legend(fontsize=fontsize, bbox_to_anchor=(1.01, 1))

	## CDF of T
	ax = axs[1]
	plot.sca(ax)
	add_cdf(T_podc_l, ax, 'PodC', next(light_color))
	add_cdf(T_ts_w_0_l, ax, 'TS, w=0', next(light_color))
	add_cdf(T_ts_w_20_l, ax, 'TS, w=20', next(light_color))
	add_cdf(T_rr_l, ax, 'RR', next(light_color))
	add_cdf(T_ucb_w_20_l, ax, 'UCB, w=20', next(light_color))
	plot.xscale('log')
	plot.ylabel('Pr{T < x}', fontsize=fontsize)
	plot.xlabel('x', fontsize=fontsize)
	legend2 = plot.legend(fontsize=fontsize, bbox_to_anchor=(1.01, 1))

	fig.set_size_inches(figsize[0], figsize[1] )
	plot.subplots_adjust(hspace=0.45, wspace=0.45)

	st = plot.suptitle(r'$d= {}, p= {}$'.format(d, p) + ', ' + get_plot_title(ro, hetero_clusters, N_fluctuating_frac, serv_time_rv), fontsize=14)
	plot.savefig(get_filename_png("plot_cdf_T_W", ro, hetero_clusters, N_fluctuating_frac, serv_time_rv), bbox_extra_artists=(st,legend1,legend2), bbox_inches='tight')
	fig.clear()

	log(INFO, "done")

def plot_cdf_T_W__podc_vs_ts_for_varying_config():
	log(INFO, "started")

	def plot_(ro, hetero_clusters):
		plot_cdf_T_W__podc_vs_ts(ro, hetero_clusters, N_fluctuating_frac=0, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]))
		plot_cdf_T_W__podc_vs_ts(ro, hetero_clusters, N_fluctuating_frac=0, serv_time_rv=Exp(serv_rate))
		plot_cdf_T_W__podc_vs_ts(ro, hetero_clusters, N_fluctuating_frac=0.3, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]))
		plot_cdf_T_W__podc_vs_ts(ro, hetero_clusters, N_fluctuating_frac=0.3, serv_time_rv=Exp(serv_rate))

	plot_(ro=0.2, hetero_clusters=False)
	plot_(ro=0.5, hetero_clusters=False)
	plot_(ro=0.8, hetero_clusters=False)
	plot_(ro=0.9, hetero_clusters=False)
	plot_(ro=0.2, hetero_clusters=True)
	plot_(ro=0.5, hetero_clusters=True)
	plot_(ro=0.8, hetero_clusters=True)
	plot_(ro=0.9, hetero_clusters=True)

	log(INFO, "done")

def plot_ET_vs_ro(hetero_clusters, N_fluctuating_frac, serv_time_rv):
	log(INFO, "started", hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv)

	ro = ''
	ro_ET_l_podc = read_json_from_file(fname=get_filename_json('{}/ro_ET_l_podc_d_{}_p_{}'.format(SUBFOLDER_PODC, d, p), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_std_T_l_podc = read_json_from_file(fname=get_filename_json('{}/ro_std_T_l_podc_d_{}_p_{}'.format(SUBFOLDER_PODC, d, p), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_ET_l_ts_w_0 = read_json_from_file(fname=get_filename_json('{}/ro_ET_l_ts_w_0'.format(SUBFOLDER_TS), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_std_T_l_ts_w_0 = read_json_from_file(fname=get_filename_json('{}/ro_std_T_l_ts_w_0'.format(SUBFOLDER_TS), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_ET_l_ts_w_20 = read_json_from_file(fname=get_filename_json('{}/ro_ET_l_ts_w_20'.format(SUBFOLDER_TS), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_std_T_l_ts_w_20 = read_json_from_file(fname=get_filename_json('{}/ro_std_T_l_ts_w_20'.format(SUBFOLDER_TS), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_ET_l_rr = read_json_from_file(fname=get_filename_json('{}/ro_ET_l_rr'.format(SUBFOLDER_RR), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_std_T_l_rr = read_json_from_file(fname=get_filename_json('{}/ro_std_T_l_rr'.format(SUBFOLDER_RR), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_ET_l_ucb_w_100 = read_json_from_file(fname=get_filename_json('{}/ro_ET_l_ucb_w_100'.format(SUBFOLDER_UCB), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	ro_std_T_l_ucb_w_100 = read_json_from_file(fname=get_filename_json('{}/ro_std_T_l_ucb_w_100'.format(SUBFOLDER_UCB), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))

	def plot_(ro_ET_l, ro_std_T_l, label):
		if ro_ET_l is None:
			return

		check(len(ro_ET_l) == len(ro_std_T_l), "ro_ET_l and ro_std_T_l must have the same size")

		ro_l, ET_l, std_T_l = [], [], []
		for i in range(len(ro_ET_l)):
			ro, ET = ro_ET_l[i]
			ro_, std_T = ro_ET_l[i]
			check(ro == ro_, "ro's should match for ET and std_T")

			ro_l.append(ro)
			ET_l.append(ET)
			std_T_l.append(std_T)
		# plot.errorbar(ro_l, ET_l, yerr=std_T_l, label=label, color=next(light_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)
		plot.plot(ro_l, ET_l, label=label, color=next(light_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	plot_(ro_ET_l_podc, ro_std_T_l_podc, label='PodC')
	plot_(ro_ET_l_ts_w_0, ro_std_T_l_ts_w_0, label='TS-ROR')
	plot_(ro_ET_l_ts_w_20, ro_std_T_l_ts_w_20, label='TS, w=20')
	plot_(ro_ET_l_rr, ro_std_T_l_rr, label='RR')
	plot_(ro_ET_l_ucb_w_100, ro_std_T_l_ucb_w_100, label='UCB, w=100')

	fontsize = 14
	plot.legend(fontsize=fontsize, bbox_to_anchor=(1.01, 1))
	plot.yscale('log')
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$\rho$', fontsize=fontsize)
	plot.title(r'$d= {}, p= {}$'.format(d, p) + ', ' + get_plot_title(ro='', hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig(get_filename_png("plot_ET_vs_ro", ro, hetero_clusters, N_fluctuating_frac, serv_time_rv), bbox_inches='tight')
	plot.gcf().clear()

	log(INFO, "done")

def plot_ET_vs_ro_for_varying_config():
	log(INFO, "started")

	hetero_clusters = False
	plot_ET_vs_ro(hetero_clusters=hetero_clusters, N_fluctuating_frac=0, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]))
	plot_ET_vs_ro(hetero_clusters=hetero_clusters, N_fluctuating_frac=0, serv_time_rv=Exp(serv_rate))
	plot_ET_vs_ro(hetero_clusters=hetero_clusters, N_fluctuating_frac=0.3, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]))
	plot_ET_vs_ro(hetero_clusters=hetero_clusters, N_fluctuating_frac=0.3, serv_time_rv=Exp(serv_rate))

	hetero_clusters = True
	plot_ET_vs_ro(hetero_clusters=hetero_clusters, N_fluctuating_frac=0, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]))
	plot_ET_vs_ro(hetero_clusters=hetero_clusters, N_fluctuating_frac=0, serv_time_rv=Exp(serv_rate))
	plot_ET_vs_ro(hetero_clusters=hetero_clusters, N_fluctuating_frac=0.3, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]))
	plot_ET_vs_ro(hetero_clusters=hetero_clusters, N_fluctuating_frac=0.3, serv_time_rv=Exp(serv_rate))

	log(INFO, "done")

def plot_T_over_time(label, cid, ro, N_fluctuating_frac, serv_time_rv, save_to_png=False):
	log(INFO, "started", label=label, cid=cid, ro=ro, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv, save_to_png=save_to_png)

	if label == 'PodC':
		req_info_m_l_podc = read_json_from_file(fname=get_filename_json('{}/req_info_m_l_{}_podc_d_{}_p_{}'.format(SUBFOLDER_PODC, cid, d, p), ro, N_fluctuating_frac, serv_time_rv))
	elif label == 'TS':
		# req_info_m_l_ts = read_json_from_file(fname=get_filename_json('{}/req_info_m_l_{}_ts'.format(SUBFOLDER_TS, cid), ro, N_fluctuating_frac, serv_time_rv))
		req_info_m_l_ts = read_json_from_file(fname=get_filename_json('{}/req_info_m_l_{}_ts_w_{}'.format(SUBFOLDER_TS, cid, w), ro, N_fluctuating_frac, serv_time_rv))
	elif label == 'RR':
		req_info_m_l_rr = read_json_from_file(fname=get_filename_json('{}/req_info_m_l_{}_rr'.format(SUBFOLDER_RR, cid), ro, N_fluctuating_frac, serv_time_rv))

	cl_id__c_m = {}
	def plot_(req_info_m_l, label):
		nonlocal cl_id__c_m
		if req_info_m_l is None:
			return

		for i, req_info_m in enumerate(req_info_m_l):
			cl_id = req_info_m['cl_id']
			if cl_id not in cl_id__c_m:
				cl_id__c_m[cl_id] = next(dark_color)
			c = cl_id__c_m[cl_id]

			if save_to_png and i > 2500:
				break

			plot.bar([i + 1], height=[req_info_m['T']], color=c) # self.color_map.get_color(info_m_q[_i]['mip'])
			plot.xticks([])

	if label == 'PodC':
		plot_(req_info_m_l_podc, label='PodC')
	elif label == 'TS':
		plot_(req_info_m_l_ts, label='TS')
	elif label == 'RR':
		plot_(req_info_m_l_rr, label='RR')

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$T$', fontsize=fontsize)
	plot.xlabel('Requests over time', fontsize=fontsize)
	plot.title(r'{}, {}, $d= {}, p= {}$'.format(label, cid, d, p) + ', ' + get_plot_title(ro, N_fluctuating_frac, serv_time_rv))

	if save_to_png:
		plot.gcf().set_size_inches(10, 4)
		plot.savefig(get_filename_png("plot_{}_T_over_time_{}".format(cid, label), ro=ro, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv), bbox_inches='tight')
		plot.gcf().clear()
	else:
		f = zoom_factory(plot.gca(), base_scale=1.5)
		plot.show()

	log(DEBUG, "done")

def plot_T_over_time_for_varying_config():
	ro = 0.8
	def plot_(label, cid):
		plot_T_over_time(label, cid, ro, N_fluctuating_frac=0, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]), save_to_png=True)
		# plot_T_over_time(label, cid, ro, N_fluctuating_frac=0, serv_time_rv=Exp(serv_rate), save_to_png=True)
		plot_T_over_time(label, cid, ro, N_fluctuating_frac=0.3, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]), save_to_png=True)
		# plot_T_over_time(label, cid, ro, N_fluctuating_frac=0, serv_time_rv=Exp(serv_rate), save_to_png=True)

	def plot_for_label(label):
		plot_(label=label, cid='c0')
		plot_(label=label, cid='c5')

	plot_for_label(label='PodC')
	plot_for_label(label='TS')
	plot_for_label(label='RR')

	log(DEBUG, "done")

def plot_cl_load_over_time(label, cl_id, ro, N_fluctuating_frac, serv_time_rv, save_to_png=False):
	log(INFO, "started", label=label, cl_id=cl_id, ro=ro, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv, save_to_png=save_to_png)

	# label = 'PodC'
	# label = 'TS'
	# label = 'RR'
	# cl_id = 'cl3'

	if label == 'PodC':
		epoch_num_req_l = read_json_from_file(fname=get_filename_json('{}/epoch_num_req_l_{}_podc_d_{}_p_{}'.format(SUBFOLDER_PODC, cl_id, d, p), ro, N_fluctuating_frac, serv_time_rv))
	elif label == 'TS':
		# epoch_num_req_l = read_json_from_file(fname=get_filename_json('{}/epoch_num_req_l_{}_ts'.format(SUBFOLDER_TS, cl_id), ro, N_fluctuating_frac, serv_time_rv))
		epoch_num_req_l = read_json_from_file(fname=get_filename_json('{}/epoch_num_req_l_{}_ts_w_{}'.format(SUBFOLDER_TS, cl_id, w), ro, N_fluctuating_frac, serv_time_rv))
	elif label == 'RR':
		epoch_num_req_l = read_json_from_file(fname=get_filename_json('{}/epoch_num_req_l_{}_rr'.format(SUBFOLDER_RR, cl_id), ro, N_fluctuating_frac, serv_time_rv))

	def plot_(epoch_num_req_l, label):
		if epoch_num_req_l is None:
			return

		epoch_l, num_req_l = [], []
		for i, (epoch, num_req) in enumerate(epoch_num_req_l):
			epoch_l.append(epoch)
			num_req_l.append(num_req)

			if save_to_png and i > 3500:
				break
		plot.plot(epoch_l, num_req_l, color=next(nice_color), marker='o', linestyle=':', lw=2, mew=3, ms=5)
	plot_(epoch_num_req_l, label)

	fontsize = 14
	plot.xticks([])
	plot.legend(fontsize=fontsize)
	plot.ylabel('Number of requests', fontsize=fontsize)
	plot.xlabel('Time', fontsize=fontsize)
	plot.title(r'{}, {}, $d= {}, p= {}, w= {}$'.format(label, cl_id, d, p, w) + ', ' + get_plot_title(ro, N_fluctuating_frac, serv_time_rv))

	if save_to_png:
		plot.gcf().set_size_inches(10, 4)
		plot.savefig(get_filename_png("plot_{}_load_over_time_{}".format(cl_id, label), ro, N_fluctuating_frac, serv_time_rv), bbox_inches='tight')
		plot.gcf().clear()
	else:
		f = zoom_factory(plot.gca(), base_scale=1.5)
		plot.show()

	log(DEBUG, "done")

def plot_cl_load_over_time_for_varying_config():
	ro = 0.8
	def plot_(label, cl_id):
		plot_cl_load_over_time(label, cl_id, ro=ro, N_fluctuating_frac=0, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]), save_to_png=True)
		# plot_cl_load_over_time(label, cl_id, ro=ro, N_fluctuating_frac=0, serv_time_rv=Exp(serv_rate), save_to_png=True)
		plot_cl_load_over_time(label, cl_id, ro=ro, N_fluctuating_frac=0.3, serv_time_rv=DiscreteRV(p_l=[1], v_l=[1 / serv_rate]), save_to_png=True)
		# plot_cl_load_over_time(label, cl_id, ro=ro, N_fluctuating_frac=0.3, serv_time_rv=Exp(serv_rate), save_to_png=True)

	def plot_for_label(label):
		plot_(label=label, cl_id='cl0')
		plot_(label=label, cl_id='cl5')
		# plot_(label=label, cl_id='cl9')

	plot_for_label(label='PodC')
	plot_for_label(label='TS')
	plot_for_label(label='RR')

	log(DEBUG, "done")

def check_bug():
	d, p = 2, 10

	ro = 0.9
	hetero_clusters = True
	N_fluctuating_frac = 0.3
	serv_time_rv = DiscreteRV(p_l=[1], v_l=[1 / serv_rate])

	T_podc_l = read_json_from_file(fname=get_filename_json('{}/T_l_podc_d_{}_p_{}'.format(SUBFOLDER_PODC, d, p), ro, hetero_clusters, N_fluctuating_frac, serv_time_rv))
	T_podc_l.sort()
	log(INFO, "", len_T_podc_l=len(T_podc_l), T_podc_l_first_20=T_podc_l[:20])

if __name__ == '__main__':
	log_to_std()

	# plot_cdf_T_W__podc_vs_ts()
	# plot_cdf_T_W__podc_vs_ts_for_varying_config()

	# plot_ET_vs_ro(N_fluctuating_frac=0.3, serv_time_rv=Exp(serv_rate))
	plot_ET_vs_ro_for_varying_config()

	# plot_T_over_time_for_varying_config()

	# plot_cl_load_over_time(N_fluctuating_frac=0.3, serv_time_rv=Exp(serv_rate))
	# plot_cl_load_over_time_for_varying_config()

	# check_bug()
