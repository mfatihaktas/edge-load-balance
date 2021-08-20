from rvs import *
from debug_utils import *

# N: # clusters
# n: # workers in each cluster
N, n = 10, 1

# m: # clients
m = 2 * N

serv_rate = 1
ro = 0.8

def get_req_gen_rate(m):
	return round(ro * N * n * serv_rate / m, 2)

req_gen_rate = get_req_gen_rate(m)
inter_req_gen_time_rv = Exp(req_gen_rate) # DiscreteRV(p_l=[1], v_l=[1 / req_gen_rate])
serv_time_rv = DiscreteRV(p_l=[1], v_l=[1 / serv_rate]) # Exp(serv_rate)

N_fluctuating_frac = 0 # 0.05 # 0 # 0.2
# net_delay = 0
# net_delay_additional = 5
net_speed = 10 * serv_rate * n
net_slowdown = 10
normal_dur_rv = DiscreteRV(p_l=[1], v_l=[int(300 * 1/serv_rate)])
slow_dur_rv = DiscreteRV(p_l=[1], v_l=[int(100 * 1/serv_rate)])
ignore_probe_cost = True

def log_sim_config():
	log(INFO, "", N=N, n=n, m=m, ro=ro, inter_req_gen_time_rv=inter_req_gen_time_rv, serv_time_rv=serv_time_rv,
			N_fluctuating_frac=N_fluctuating_frac, net_speed=net_speed, net_slowdown=net_slowdown,
			normal_dur_rv=normal_dur_rv, slow_dur_rv=slow_dur_rv, ignore_probe_cost=ignore_probe_cost)

def get_inter_req_gen_time_rv(m):
	return Exp(get_req_gen_rate(m))

def get_plot_title():
	return r'$N= {}, n= {}, N_f= {}, m= {}$'.format(N, n, int(N * N_fluctuating_frac), m) + '\n' + \
				 r'$X \sim {}$, $S \sim {}$'.format(inter_req_gen_time_rv, serv_time_rv)

def get_filename_tail():
	return 'N_{}'.format(N) + \
				 '_n_{}'.format(n) + \
				 '_m_{}'.format(m) + \
				 '_ro_{}'.format(ro) + \
				 '_Nff_{}'.format(N_fluctuating_frac) + \
				 '_netSlowdown_{}'.format(net_slowdown) + \
				 '_ignoreProbeCost_{}'.format(ignore_probe_cost) + \
				 '_S_{}'.format(serv_time_rv)

def get_filename_png(header):
	return header + '__' + get_filename_tail() + '.png'

def get_filename_json(header):
	return header + '__' + get_filename_tail() + '.json'
