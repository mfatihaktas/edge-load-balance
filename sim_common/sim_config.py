from rvs import *
from debug_utils import *

# N: # clusters
# n: # workers in each cluster
N, n = 10, 1

# m: # clients
m = 2 * N

serv_rate = 1
ro = 0.8
hetero_clusters = False
# hetero_clusters = True

def get_req_gen_rate(ro, m):
	return round(ro * N * n * serv_rate / m, 2)

req_gen_rate = get_req_gen_rate(ro, m)
inter_req_gen_time_rv = Exp(req_gen_rate) # DiscreteRV(p_l=[1], v_l=[1 / req_gen_rate])
serv_time_rv = DiscreteRV(p_l=[1], v_l=[1 / serv_rate])
# serv_time_rv = Exp(serv_rate)

N_fluctuating_frac = 0
# N_fluctuating_frac = 0.3
# worker_slowdown = 5
worker_slowdown = 10
normal_dur_rv = DiscreteRV(p_l=[1], v_l=[int(300 * 1/serv_rate)])
slow_dur_rv = DiscreteRV(p_l=[1], v_l=[int(100 * 1/serv_rate)])
ignore_probe_cost = True

def set_sim_config(config_m):
	global hetero_clusters, serv_time_rv, N_fluctuating_frac
	log(INFO, "started", config_m=config_m)

	if 'hetero_clusters' in config_m:
		hetero_clusters = config_m['hetero_clusters']
	if 'N_fluctuating_frac' in config_m:
		N_fluctuating_frac = config_m['N_fluctuating_frac']

	if 'serv_time_rv' in config_m:
		if config_m['serv_time_rv'] == 'disc':
			serv_time_rv = DiscreteRV(p_l=[1], v_l=[1 / serv_rate])
		elif config_m['serv_time_rv'] == 'exp':
			serv_time_rv = Exp(serv_rate)

	log(INFO, "done")

def log_sim_config():
	log(INFO, "", N=N, n=n, m=m, ro=ro, hetero_clusters=hetero_clusters,
			inter_req_gen_time_rv=inter_req_gen_time_rv, serv_time_rv=serv_time_rv,
			N_fluctuating_frac=N_fluctuating_frac, worker_slowdown=worker_slowdown,
			normal_dur_rv=normal_dur_rv, slow_dur_rv=slow_dur_rv, ignore_probe_cost=ignore_probe_cost)

def get_inter_req_gen_time_rv(ro, m):
	return Exp(get_req_gen_rate(ro, m))

def get_plot_title(ro=ro, hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv):
	return r'$\rho= {}, N= {}, n= {}, N_f= {}, m= {}, h= {}$'.format(ro, N, n, int(N * N_fluctuating_frac), m, hetero_clusters) + '\n' + \
				 r'$X \sim {}$, $S \sim {}$'.format(inter_req_gen_time_rv, serv_time_rv)

def get_filename_tail(ro=ro, hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv):
	# return 'N_{}'.format(N) + \
	# 			 '_n_{}'.format(n) + \
	# 			 '_m_{}'.format(m) + \
	# 			 '_ro_{}'.format(ro) + \
	# 			 '_Nff_{}'.format(N_fluctuating_frac) + \
	# 			 '_workerSlowdown_{}'.format(worker_slowdown) + \
	# 			 '_ignoreProbeCost_{}'.format(ignore_probe_cost) + \
	# 			 '_S_{}'.format(serv_time_rv)
  return 'N_{}'.format(N) + \
				 '_n_{}'.format(n) + \
				 '_m_{}'.format(m) + \
				 '_h_{}'.format(hetero_clusters) + \
				 '_ro_{}'.format(ro) + \
				 '_Nff_{}'.format(N_fluctuating_frac) + \
				 '_workerSlowdown_{}'.format(worker_slowdown) + \
				 '_ignoreProbeCost_{}'.format(ignore_probe_cost) + \
				 '_S_{}'.format(serv_time_rv)

def get_filename_png(header, ro=ro, hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv):
	return header + '__' + get_filename_tail(ro, hetero_clusters, N_fluctuating_frac, serv_time_rv) + '.png'

def get_filename_json(header, ro=ro, hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv):
	return header + '__' + get_filename_tail(ro, hetero_clusters, N_fluctuating_frac, serv_time_rv) + '.json'
