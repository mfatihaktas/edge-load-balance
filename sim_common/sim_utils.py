import getopt, json, math
import numpy as np

from cluster import *
from worker import *
import sim_config
import file_utils
from plot_utils import *

def get_cl_l(env):
	if sim_config.hetero_clusters:
		if sim_config.N == 10:
			speed_l = [1, 1, 0.5, 1.5, 0.25, 1.75, 0.3, 1.7, 0.1, 1.9]
		else:
			assert_("Unexpected N", N=N)
	else:
		speed_l = sim_config.N * [1]

	Nf = int(sim_config.N * sim_config.N_fluctuating_frac)
	cl_l = [Cluster('cl{}'.format(i), env, sim_config.n, speed_l[i], sim_config.worker_slowdown, sim_config.normal_dur_rv, sim_config.slow_dur_rv, sim_config.ignore_probe_cost) for i in range(Nf)]
	for i in range(Nf, sim_config.N):
		cl_l.append(Cluster('cl{}'.format(i), env, sim_config.n, speed_l[i], ignore_probe_cost=sim_config.ignore_probe_cost))

	return cl_l

def get_stats_m_from_sim_data(cl_l, c_l, header=None, ro=sim_config.ro):
	log(INFO, "started")

	if header is not None:
		for cl in cl_l:
			file_utils.write_to_file(data=json.dumps(cl.master.epoch_num_req_l), fname=sim_config.get_filename(header='epoch_num_req_l_{}_{}'.format(cl._id, header), ext='json', ro_arg=ro))

	t_l, w_l, rw_l = [], [], []
	for c in c_l:
		req_info_m_l = []
		for req in c.req_finished_l:
			t = req.epoch_arrived_client - req.epoch_departed_client
			w = t - req.serv_time
			rw = req.chosen_wait_time - req.min_wait_time

			t_l.append(t)
			w_l.append(w)
			if rw < 0:
				log(WARNING, "Regret-waiting time is not supposed to be negative", rw=rw)
			else:
				rw_l.append(rw)

			if header is not None:
				req_info_m_l.append({
					'req_id': req._id,
					'cl_id': req.cl_id,
					'epoch_arrived_client': req.epoch_arrived_client,
					'T': t, 'W': w,
					'min_wait_time': req.min_wait_time, 'chosen_wait_time': req.chosen_wait_time})
		if header is not None:
			file_utils.write_to_file(data=json.dumps(req_info_m_l), fname=sim_config.get_filename(header='req_info_m_l_{}_{}'.format(c._id, header), ext='json', ro_arg=ro))

	if header is not None:
		file_utils.write_to_file(data=json.dumps(t_l), fname=sim_config.get_filename(header='T_l_{}'.format(header), ext='json', ro_arg=ro))
		file_utils.write_to_file(data=json.dumps(w_l), fname=sim_config.get_filename(header='W_l_{}'.format(header), ext='json', ro_arg=ro))
		file_utils.write_to_file(data=json.dumps(rw_l), fname=sim_config.get_filename(header='RW_l_{}'.format(header), ext='json', ro_arg=ro))

	ET, std_T = np.mean(t_l), np.std(t_l)
	EW, std_W = np.mean(w_l), np.std(w_l)
	ERW, std_RW = np.mean(rw_l), np.std(rw_l)
	return {'ET': ET, 'std_T': std_T,
					'EW': EW, 'std_W': std_W,
					'ERW': ERW, 'std_RW': std_RW}

def sim_common_w_construct_client(label, construct_client, num_req_to_finish=sim_config.num_req_to_finish, ro=sim_config.ro, num_sim=sim_config.num_sim, write_to_json=False):
	log(DEBUG, "started", label=label, num_req_to_finish=num_req_to_finish, ro=ro, num_sim=num_sim, write_to_json=write_to_json)

	inter_req_gen_time_rv = sim_config.get_inter_req_gen_time_rv(ro)

	cum_ET, cum_std_T = 0, 0
	cum_EW, cum_std_W = 0, 0
	cum_ERW, cum_std_RW = 0, 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run".format(i))

		env = simpy.Environment()
		cl_l = get_cl_l(env)
		c_l = [construct_client(j, env, cl_l, inter_req_gen_time_rv) for j in range(sim_config.m)]
		net = Net('n', env, [*cl_l, *c_l])
		env.run(until=c_l[0].act_recv)

		stats_m = get_stats_m_from_sim_data(cl_l, c_l, header=label if write_to_json else None, ro=ro)

		ET, std_T = stats_m['ET'], stats_m['std_T']
		EW, std_W = stats_m['EW'], stats_m['std_W']
		ERW, std_RW = stats_m['ERW'], stats_m['std_RW']
		log(INFO, "", ET=ET, std_T=std_T, EW=EW, std_W=std_W, ERW=ERW, std_RW=std_RW)
		cum_ET += ET
		cum_std_T += std_T
		cum_EW += EW
		cum_std_W += std_W
		cum_ERW += ERW
		cum_std_RW += std_RW

	log(INFO, "done")
	return {'ET': cum_ET / num_sim, 'std_T': cum_std_T / num_sim,
					'EW': cum_EW / num_sim, 'std_W': cum_std_W / num_sim,
					'ERW': cum_ERW / num_sim, 'std_RW': cum_std_RW / num_sim}

def sim_common_ET_vs_ro(label, sim_w_ro):
	# num_req_to_finish = 10000
	# num_sim = 2 # 10
	log(DEBUG, "started", num_req_to_finish=sim_config.num_req_to_finish, num_sim=sim_config.num_sim, label=label, sim_w_ro=sim_w_ro)

	ro_l, ET_l, std_T_l, EW_l, std_W_l, ERW_l, std_RW_l = [], [], [], [], [], [], []
	for ro in sim_config.RO_l:
		log(INFO, "> ro= {}".format(ro))
		ro_l.append(ro)

		m = sim_w_ro(ro)
		ET, std_T, EW, std_W, ERW, std_RW = m['ET'], m['std_T'], m['EW'], m['std_W'], m['ERW'], m['std_RW']
		log(INFO, "", ET=ET, std_T=std_T, EW=EW, std_W=std_W, ERW=ERW, std_RW=std_RW)
		ET_l.append(ET)
		std_T_l.append(std_T)
		EW_l.append(EW)
		std_W_l.append(std_W)
		ERW_l.append(ERW)
		std_RW_l.append(std_RW)

	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, ET_l))), fname=sim_config.get_filename(header='ro_ET_l_{}'.format(label), ext='json', ro_arg=''))
	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, std_T_l))), fname=sim_config.get_filename(header='ro_std_T_l_{}'.format(label), ext='json', ro_arg=''))
	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, EW_l))), fname=sim_config.get_filename(header='ro_EW_l_{}'.format(label), ext='json', ro_arg=''))
	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, std_W_l))), fname=sim_config.get_filename(header='ro_std_W_l_{}'.format(label), ext='json', ro_arg=''))
	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, ERW_l))), fname=sim_config.get_filename(header='ro_ERW_l_{}'.format(label), ext='json', ro_arg=''))
	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, std_RW_l))), fname=sim_config.get_filename(header='ro_std_RW_l_{}'.format(label), ext='json', ro_arg=''))

	plot.errorbar(ro_l, ET_l, yerr=std_T_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$\rho$', fontsize=fontsize)
	plot.title('{}'.format(label) + ', ' + sim_config.get_plot_title())
	plot.gcf().set_size_inches(6, 4)
	plot.savefig(sim_config.get_filename("plot_ET_vs_ro_{}".format(label), ext='png'), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

def parse_argv_for_sim(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['hetero_clusters=', 'N_fluctuating_frac=', 'serv_time_rv='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		print("opt= {},\n	 arg= {}".format(opt, arg))
		if opt == '--hetero_clusters':
			m['hetero_clusters'] = bool(int(arg))
		elif opt == '--N_fluctuating_frac':
			m['N_fluctuating_frac'] = float(arg)
		elif opt == '--serv_time_rv':
			m['serv_time_rv'] = arg
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	log(DEBUG, "", m=m)
	return m
