from rvs import *
from debug_utils import *

# N: # clusters
# n: # workers in each cluster
N, n = 10, 1

# m: # clients
m = 1 # 2 * N

ro = 0.8
req_gen_rate = get_req_gen_rate(m)
inter_req_gen_time_rv = Exp(req_gen_rate) # DiscreteRV(p_l=[1], v_l=[1 / req_gen_rate])
serv_rate = 1
serv_time_rv = Exp(serv_rate) # DiscreteRV(p_l=[1], v_l=[1 / serv_rate])

def log_global_vars():
	log(DEBUG, "", N=N, n=n, m=m, ro=ro, inter_req_gen_time_rv=inter_req_gen_time_rv, serv_time_rv=serv_time_rv)

def get_req_gen_rate(m):
	return round(ro * N * n / m, 2)

def get_inter_req_gen_time_rv(m):
	return Exp(get_req_gen_rate(m))
