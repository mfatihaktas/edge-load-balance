from cluster import *
from worker import *
from sim_config import *

def get_cl_l(env):
	Nf = int(N * N_fluctuating_frac)
	cl_l = [Cluster('cl{}'.format(i), env, n, ignore_probe_cost, worker_slowdown, normal_dur_rv, slow_dur_rv) for i in range(Nf)]
	for i in range(Nf, N):
		cl_l.append(Cluster('cl{}'.format(i), env, n, ignore_probe_cost))

	return cl_l
