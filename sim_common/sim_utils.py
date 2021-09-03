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
	sim_config.log_sim_config()

	if header is not None:
		for cl in cl_l:
			file_utils.write_to_file(data=json.dumps(cl.master.epoch_num_req_l), fname=sim_config.get_filename_json(header='epoch_num_req_l_{}_{}'.format(cl._id, header), ro_arg=ro))

	t_l, t2_l = [], []
	w_l, w2_l = [], []
	for c in c_l:
		req_info_m_l = []
		for req in c.req_finished_l:
			t = req.epoch_arrived_client - req.epoch_departed_client
			w = t - req.serv_time

			t_l.append(t)
			t2_l.append(t**2)
			w_l.append(t - req.serv_time)
			w2_l.append(w**2)

			if header is not None:
				req_info_m_l.append({
					'req_id': req._id,
					'cl_id': req.cl_id,
					'epoch_arrived_client': req.epoch_arrived_client,
					'T': t, 'W': w})
		if header is not None:
			file_utils.write_to_file(data=json.dumps(req_info_m_l), fname=sim_config.get_filename_json(header='req_info_m_l_{}_{}'.format(c._id, header), ro_arg=ro))

	if header is not None:
		file_utils.write_to_file(data=json.dumps(t_l), fname=sim_config.get_filename_json(header='T_l_{}'.format(header), ro_arg=ro))
		file_utils.write_to_file(data=json.dumps(w_l), fname=sim_config.get_filename_json(header='W_l_{}'.format(header), ro_arg=ro))

	ET, ET2 = np.mean(t_l), np.mean(t2_l)
	EW, EW2 = np.mean(w_l), np.mean(w2_l)
	std_T = math.sqrt(ET2 - ET**2) if ET2 - ET**2 > 0 else 0
	std_W = math.sqrt(EW2 - EW**2) if EW2 - EW**2 > 0 else 0
	return {'ET': ET, 'std_T': std_T,
					'EW': EW, 'std_W': std_W}

def sim_common_w_construct_client(label, construct_client, num_req_to_finish=sim_config.num_req_to_finish, ro=sim_config.ro, num_sim=sim_config.num_sim, write_to_json=False):
	log(DEBUG, "started", label=label, num_req_to_finish=num_req_to_finish, ro=ro, num_sim=num_sim, write_to_json=write_to_json)

	inter_req_gen_time_rv = sim_config.get_inter_req_gen_time_rv(ro)

	cum_ET, cum_std_T = 0, 0
	cum_EW, cum_std_W = 0, 0
	for i in range(num_sim):
		log(DEBUG, "*** {}th sim run started".format(i))

		env = simpy.Environment()
		cl_l = get_cl_l(env)
		c_l = [construct_client(j, env, cl_l, inter_req_gen_time_rv) for j in range(sim_config.m)]
		net = Net('n', env, [*cl_l, *c_l])
		env.run(until=c_l[0].act_recv)

		stats_m = get_stats_m_from_sim_data(cl_l, c_l, header=label if write_to_json else None, ro=ro)

		ET, std_T = stats_m['ET'], stats_m['std_T']
		EW, std_W = stats_m['EW'], stats_m['std_W']
		log(INFO, "", ET=ET, std_T=std_T, EW=EW, std_W=std_W)
		cum_ET += ET
		cum_std_T += std_T
		cum_EW += EW
		cum_std_W += std_W

	log(INFO, 'done')
	return cum_ET / num_sim, cum_std_T / num_sim, cum_EW / num_sim, cum_std_W / num_sim

def sim_common_ET_vs_ro(label, sim_w_ro):
	# num_req_to_finish = 10000
	# num_sim = 2 # 10
	log(DEBUG, "started", num_req_to_finish=sim_config.num_req_to_finish, num_sim=sim_config.num_sim, label=label, sim_w_ro=sim_w_ro)

	sim_config.log_sim_config()

	ro_l, ET_l, std_T_l, EW_l, std_W_l = [], [], [], [], []
	for ro in [0.2, 0.5, 0.65, 0.8, 0.9]:
		log(INFO, "> ro= {}".format(ro))
		ro_l.append(ro)

		ET, std_T, EW, std_W = sim_w_ro(ro)
		log(INFO, "", ET=ET, std_T=std_T, EW=EW, std_W=std_W)
		ET_l.append(ET)
		std_T_l.append(std_T)
		EW_l.append(EW)
		std_W_l.append(std_W)

	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, ET_l))), fname=sim_config.get_filename_json(header='ro_ET_l_{}'.format(label), ro_arg=''))
	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, std_T_l))), fname=sim_config.get_filename_json(header='ro_std_T_l_{}'.format(label), ro_arg=''))
	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, EW_l))), fname=sim_config.get_filename_json(header='ro_EW_l_{}'.format(label), ro_arg=''))
	file_utils.write_to_file(data=json.dumps(list(zip(ro_l, std_W_l))), fname=sim_config.get_filename_json(header='ro_std_W_l_{}'.format(label), ro_arg=''))

	plot.errorbar(ro_l, ET_l, yerr=std_T_l, color=next(nice_color), marker='x', linestyle='solid', lw=2, mew=3, ms=5)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[T]$', fontsize=fontsize)
	plot.xlabel(r'$\rho$', fontsize=fontsize)
	plot.title('{}'.format(label) + ', ' + sim_config.get_plot_title())
	plot.gcf().set_size_inches(6, 4)
	plot.savefig(sim_config.get_filename_png("plot_ET_vs_ro_{}".format(label)), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

def parse_argv_for_sim(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['hetero_clusters=', 'N_fluctuating_frac=', 'serv_time_rv='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		print("opt= {},\n  arg= {}".format(opt, arg))
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
