from rvs import *
from debug_utils import *

# N: # clusters
# n: # workers in each cluster
N, n = 10, 1

# m: # clients
m = 1 # 2 * N

ro = 0.8

def get_req_gen_rate(m):
	return round(ro * N * n / m, 2)

req_gen_rate = get_req_gen_rate(m)
inter_req_gen_time_rv = Exp(req_gen_rate) # DiscreteRV(p_l=[1], v_l=[1 / req_gen_rate])
serv_rate = 1
serv_time_rv = Exp(serv_rate) # DiscreteRV(p_l=[1], v_l=[1 / serv_rate])

fluctuating_net_state = True # False
net_delay = 0
net_delay_additional = 5
num_fluctuating_cl = 2
normal_dur_rv = DiscreteRV(p_l=[1], v_l=[100])
slow_dur_rv = DiscreteRV(p_l=[1], v_l=[100])

def log_global_vars():
	log(INFO, "", N=N, n=n, m=m, ro=ro, inter_req_gen_time_rv=inter_req_gen_time_rv, serv_time_rv=serv_time_rv,
			fluctuating_net_state=fluctuating_net_state, net_delay=net_delay, net_delay_additional=net_delay_additional,
			num_fluctuating_cl=num_fluctuating_cl, normal_dur_rv=normal_dur_rv, slow_dur_rv=slow_dur_rv)

def get_inter_req_gen_time_rv(m):
	return Exp(get_req_gen_rate(m))
