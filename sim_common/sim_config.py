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

def get_req_gen_rate(ro):
	return round(ro * N * n * serv_rate / m, 2)

def get_inter_req_gen_time_rv(ro):
	return Exp(get_req_gen_rate(ro))

inter_req_gen_time_rv = get_inter_req_gen_time_rv(ro)
serv_time_rv = DiscreteRV(p_l=[1], v_l=[1 / serv_rate])
# serv_time_rv = Exp(serv_rate)

N_fluctuating_frac = round(0.0, 1)
# N_fluctuating_frac = 0.3
# worker_slowdown = 5
worker_slowdown = 10
normal_dur_rv = DiscreteRV(p_l=[1], v_l=[int(300 * 1/serv_rate)])
slow_dur_rv = DiscreteRV(p_l=[1], v_l=[int(100 * 1/serv_rate)])
ignore_probe_cost = True

# num_req_to_finish = 10
# num_req_to_finish = 10000
num_req_to_finish = 15000
# num_sim = 1
num_sim = 2
# num_sim = 3

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

def get_plot_title(ro=None, hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv):
	# return r'$\rho= {}, $'.format(ro) if ro is not None else '' + \
  #        r'$N= {}, n= {}, N_f= {}, m= {}, h= {}$'.format(N, n, int(N * N_fluctuating_frac), m, hetero_clusters) + '\n' + \
	# 			 r'$X \sim Exp$, $S \sim {}$'.format(serv_time_rv)
	# return r'$\rho= {}, $'.format(ro) if ro is not None else '' + \
	# 			 r'$N= {}, n= {}, N_f= {}, m= {}, S \sim {}$'.format(N, n, int(N * N_fluctuating_frac), m, serv_time_rv)
	return r'$\rho= {}, N= {}, n= {}, N_f= {}, m= {}, S \sim {}$'.format(ro, N, n, int(N * N_fluctuating_frac), m, serv_time_rv)

def get_filename_tail(ro=ro, hetero_clusters=hetero_clusters, N_fluctuating_frac=N_fluctuating_frac, serv_time_rv=serv_time_rv):
	return 'N_{}'.format(N) + \
				 '_n_{}'.format(n) + \
				 '_m_{}'.format(m) + \
				 '_h_{}'.format(hetero_clusters) + \
				 '_ro_{}'.format(ro) + \
				 '_Nff_{:.1f}'.format(N_fluctuating_frac) + \
				 '_workerSlowdown_{}'.format(worker_slowdown) + \
				 '_ignoreProbeCost_{}'.format(ignore_probe_cost) + \
				 '_S_{}'.format(serv_time_rv)

def get_filename(header, extension, ro_arg=None, hetero_clusters_arg=None, N_fluctuating_frac_arg=None, serv_time_rv_arg=None):
	return header + '__' + get_filename_tail(ro if ro_arg is None else ro_arg,
																					 hetero_clusters if hetero_clusters_arg is None else hetero_clusters_arg,
																					 N_fluctuating_frac if N_fluctuating_frac_arg is None else N_fluctuating_frac_arg,
																					 serv_time_rv if serv_time_rv_arg is None else serv_time_rv_arg) + \
																					 '.' + extension

def get_filename_png(header, ro_arg=None, hetero_clusters_arg=None, N_fluctuating_frac_arg=None, serv_time_rv_arg=None):
	return get_filename(header, 'png', ro_arg, hetero_clusters_arg, N_fluctuating_frac_arg, serv_time_rv_arg)

def get_filename_pdf(header, ro_arg=None, hetero_clusters_arg=None, N_fluctuating_frac_arg=None, serv_time_rv_arg=None):
	return get_filename(header, 'pdf', ro_arg, hetero_clusters_arg, N_fluctuating_frac_arg, serv_time_rv_arg)

def get_filename_json(header, ro_arg=None, hetero_clusters_arg=None, N_fluctuating_frac_arg=None, serv_time_rv_arg=None):
	return header + '__' + get_filename_tail(ro if ro_arg is None else ro_arg,
																					 hetero_clusters if hetero_clusters_arg is None else hetero_clusters_arg,
																					 N_fluctuating_frac if N_fluctuating_frac_arg is None else N_fluctuating_frac_arg,
																					 serv_time_rv if serv_time_rv_arg is None else serv_time_rv_arg) + '.json'
