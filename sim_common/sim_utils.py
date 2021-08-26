from cluster import *
from worker import *
from sim_config import *

def get_cl_l(env):
	Nf = int(N * N_fluctuating_frac)
	cl_l = [Cluster('cl{}'.format(i), env, n, ignore_probe_cost, worker_slowdown, normal_dur_rv, slow_dur_rv) for i in range(Nf)]
	for i in range(Nf, N):
		cl_l.append(Cluster('cl{}'.format(i), env, n, ignore_probe_cost))

	return cl_l

def get_stats_m_from_sim_data(c_l, header=None):
	t_l, w_l = [], []
	for c in c_l:
		req_info_m_l = []
		for req in c.req_finished_l:
			t = req.epoch_arrived_client - req.epoch_departed_client
			t_l.append(t)
			w_l.append(t - req.serv_time)

			if header is not None:
				req_info_m_l.append({
					'rid': req._id,
					'mid': req.mid,
					'epoch_arrived_client': req.epoch_arrived_client,
					'T': t,
					'W': t - req.serv_time})
		if header is not None:
			write_to_file(data=json.dumps(req_info_m_l), fname=get_filename_json(header='req_info_m_l_{}'.format(header)))

	if header is not None:
		write_to_file(data=json.dumps(t_l), fname=get_filename_json(header='T_l_{}'.format(header)))
		write_to_file(data=json.dumps(w_l), fname=get_filename_json(header='W_l_{}'.format(header)))

	return {'ET': np.mean(t_l), 'EW': np.mean(w_l)}
