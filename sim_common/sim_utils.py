import getopt

from cluster import *
from worker import *
from sim_config import *

def get_cl_l(env):
	if hetero_clusters:
		if N == 10:
			speed_l = [1, 1, 0.5, 1.5, 0.25, 1.75, 0.3, 1.7, 0.1, 1.9]
		else:
			assert_("Unexpected N", N=N)
	else:
		speed_l = N * [1]

	Nf = int(N * N_fluctuating_frac)
	cl_l = [Cluster('cl{}'.format(i), env, n, speed_l[i], worker_slowdown, normal_dur_rv, slow_dur_rv, ignore_probe_cost) for i in range(Nf)]
	for i in range(Nf, N):
		cl_l.append(Cluster('cl{}'.format(i), env, n, speed_l[i], ignore_probe_cost=ignore_probe_cost))

	return cl_l

def get_stats_m_from_sim_data(cl_l, c_l, header=None, ro=ro):
	if header is not None:
		for cl in cl_l:
			write_to_file(data=json.dumps(cl.master.epoch_num_req_l), fname=get_filename_json(header='epoch_num_req_l_{}_{}'.format(cl._id, header), ro=ro))

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
			write_to_file(data=json.dumps(req_info_m_l), fname=get_filename_json(header='req_info_m_l_{}_{}'.format(c._id, header), ro=ro))

	if header is not None:
		write_to_file(data=json.dumps(t_l), fname=get_filename_json(header='T_l_{}'.format(header), ro=ro))
		write_to_file(data=json.dumps(w_l), fname=get_filename_json(header='W_l_{}'.format(header), ro=ro))

	ET, ET2 = np.mean(t_l), np.mean(t2_l)
	EW, EW2 = np.mean(w_l), np.mean(w2_l)
	std_T = math.sqrt(ET2 - ET**2) if ET2 - ET**2 > 0 else 0
	std_W = math.sqrt(EW2 - EW**2) if EW2 - EW**2 > 0 else 0
	return {'ET': ET, 'std_T': std_T,
					'EW': EW, 'std_W': std_W}

def parse_argv_for_sim(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['hetero_clusters=', 'N_fluctuating_frac=', 'serv_time_rv='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		print("opt= {},\n  arg= {}".format(opt, arg))
		if opt == '--hetero_clusters':
			m['hetero_clusters'] = bool(arg)
		elif opt == '--N_fluctuating_frac':
			m['N_fluctuating_frac'] = float(arg)
		elif opt == '--serv_time_rv':
			m['serv_time_rv'] = arg
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	log(DEBUG, "", m=m)
	return m
