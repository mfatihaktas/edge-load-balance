import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy, random, math, scipy
from collections import deque
from collections import defaultdict
import numpy as np

from msg import *
from rvs import Normal
from debug_utils import *

class UCB_slidingWin():
	def __init__(self, arm_id_l, win_len, percentile=0.1):
		self.arm_id_l = arm_id_l
		self.win_len = win_len
		self.percentile = percentile

		self.arm_id_cost_q = deque(maxlen=win_len)
		for arm_id in self.arm_id_l:
			self.arm_id_cost_q.append((arm_id, 0))

	def __repr__(self):
		return 'UCB_slidingWin(arm_id_l= {}, win_len= {}, percentile= {})'.format(self.arm_id_l, self.win_len, self.percentile)

	def record_cost(self, arm_id, cost):
		self.arm_id_cost_q.append((arm_id, cost))
		log(DEBUG, "recorded", arm_id=arm_id, cost=cost)

	## Deprecated
	def __sample_arm(self):
		arm_id__cost_l_m = defaultdict(list)
		for (arm_id, cost) in self.arm_id_cost_q:
			arm_id__cost_l_m[arm_id].append(cost)

		log(DEBUG, "", arm_id__cost_l_m=arm_id__cost_l_m)

		min_arm_id, min_cost = None, float('Inf')
		log(DEBUG, "len(arm_id__cost_l_m)= {}".format(len(arm_id__cost_l_m)))
		for arm_id, cost_l in arm_id__cost_l_m.items():
			exploit_cost = np.mean(cost_l) if len(cost_l) else 0 / len(cost_l)
			explore_cost = 10 * math.sqrt(math.log(len(self.arm_id_cost_q)) / len(cost_l))
			cost = exploit_cost + explore_cost
			if cost < min_cost:
				min_cost = cost
				min_arm_id = arm_id
				log(DEBUG, "cost < min_cost", cost=cost, exploit_cost=exploit_cost, explore_cost=explore_cost, min_cost=min_cost, min_arm_id=min_arm_id)
		return min_arm_id

	def sample_arm(self):
		arm_id__cost_l_m = defaultdict(list)
		for (arm_id, cost) in self.arm_id_cost_q:
			arm_id__cost_l_m[arm_id].append(cost)

		log(DEBUG, "", arm_id__cost_l_m=arm_id__cost_l_m)

		min_arm_id, min_cost = None, float('Inf')
		log(DEBUG, "len(arm_id__cost_l_m)= {}".format(len(arm_id__cost_l_m)))
		for arm_id, cost_l in arm_id__cost_l_m.items():
			mean = np.mean(cost_l) if len(cost_l) else 0
			stdev = np.std(cost_l) if len(cost_l) else 1
			if stdev == 0:
				stdev = 1

			cost = scipy.stats.norm.ppf(self.percentile, loc=mean, scale=stdev)
			if cost < min_cost:
				log(DEBUG, "cost < min_cost", cost=cost, arm_id=arm_id, min_cost=min_cost, min_arm_id=min_arm_id)
				min_cost = cost
				min_arm_id = arm_id

		return min_arm_id

class UCB_slidingWinAtEachArm():
	def __init__(self, arm_id_l, win_len, percentile=0.1):
		self.arm_id_l = arm_id_l
		self.win_len = win_len
		self.percentile = percentile

		self.arm_id__cost_q_m = {i: deque(maxlen=win_len) for i in arm_id_l}

	def __repr__(self):
		return 'UCB_slidingWinAtEachArm(arm_id_l= {}, win_len= {}, percentile= {})'.format(self.arm_id_l, self.win_len, self.percentile)

	def record_cost(self, arm_id, cost):
		self.arm_id__cost_q_m[arm_id].append(cost)
		log(DEBUG, "recorded", arm_id=arm_id, cost=cost)

	## Deprecated
	def __sample_arm(self):
		log(DEBUG, "", arm_id__cost_q_m=self.arm_id__cost_q_m)

		## Would be slow
		# t = sum(len(cost_q) for _, cost_q in arm_id__cost_q_m.items())
		t = len(self.arm_id_l) * self.win_len
		min_arm_id, min_cost = None, float('Inf')
		for arm_id, cost_q in self.arm_id__cost_q_m.items():
			exploit_cost = np.mean(cost_q) / len(cost_q) if len(cost_q) else 0
			explore_cost = 10 * math.sqrt(math.log(t) / len(cost_q)) if len(cost_q) else 0
			cost = exploit_cost + explore_cost
			if cost < min_cost:
				min_cost = cost
				min_arm_id = arm_id
				log(DEBUG, "cost < min_cost", cost=cost, exploit_cost=exploit_cost, explore_cost=explore_cost, min_cost=min_cost, min_arm_id=min_arm_id)

		return min_arm_id

	def sample_arm(self):
		log(DEBUG, "", arm_id__cost_q_m=self.arm_id__cost_q_m)

		min_arm_id, min_cost = None, float('Inf')
		for arm_id, cost_q in self.arm_id__cost_q_m.items():
			mean = np.mean(cost_q) if len(cost_q) else 0
			stdev = np.std(cost_q) if len(cost_q) else 1
			if stdev == 0:
				stdev = 1

			cost = scipy.stats.norm.ppf(self.percentile, loc=mean, scale=stdev)
			# log(WARNING, "", mean=mean, stdev=stdev, cost=cost)
			if cost < min_cost:
				log(DEBUG, "cost < min_cost", cost=cost, arm_id=arm_id, min_cost=min_cost, min_arm_id=min_arm_id)
				min_cost = cost
				min_arm_id = arm_id

		return min_arm_id

class UCB_resetWindowOnRareEvent():
	def __init__(self, arm_id_l, percentile=0.1, threshold_prob_rare=0.9):
		self.arm_id_l = arm_id_l
		self.percentile = percentile
		self.threshold_prob_rare = threshold_prob_rare

		self.arm_id__n_mean_var_m = {i: (0, 0, 1) for i in arm_id_l}

	def __repr__(self):
		return 'UCB_resetWindowOnRareEvent(arm_id_l= {}, percentile= {})'.format(self.arm_id_l, self.percentile)

	def record_cost(self, arm_id, cost):
		n, _mean, _var = self.arm_id__n_mean_var_m[arm_id]

		def record():
			mean = (_mean * n + cost) / (n + 1)
			## https://math.stackexchange.com/questions/102978/incremental-computation-of-standard-deviation
			var = (n - 1)/n * _var + (cost - _mean)**2 / (n + 1) if n > 0 else 1
			self.arm_id__n_mean_var_m[arm_id] = (n + 1, mean, var)

			log(DEBUG, "Recorded", cost=cost, n=n, _mean=_mean, _var=_var, mean=mean, var=var)

		if n < 6:
			record()
			return

		_stdev = math.sqrt(_var)
		cost_rv = Normal(_mean, _stdev)
		Pr_getting_larger_than_cost = cost_rv.tail(cost)
		Pr_getting_smaller_than_cost = cost_rv.cdf(cost)
		Pr_cost_is_rare = 1 - min(Pr_getting_larger_than_cost, Pr_getting_smaller_than_cost)
		if Pr_cost_is_rare >= self.threshold_prob_rare:
			log(DEBUG, "Rare event detected", cost=cost, _mean=_mean, _stdev=_stdev, Pr_cost_is_rare=Pr_cost_is_rare, threshold_prob_rare=self.threshold_prob_rare)
			self.arm_id__n_mean_var_m[arm_id] = (1, cost, 1)
		else:
			record()

		log(DEBUG, "recorded", arm_id=arm_id, cost=cost)

	def sample_arm(self):
		log(DEBUG, "", arm_id__n_mean_var_m=self.arm_id__n_mean_var_m)

		min_arm_id, min_cost = None, float('Inf')
		for arm_id, (n, mean, var) in self.arm_id__n_mean_var_m.items():
			stdev = math.sqrt(var) if var > 0 else 1

			cost = scipy.stats.norm.ppf(self.percentile, loc=mean, scale=stdev)
			if cost < min_cost:
				log(DEBUG, "cost < min_cost", cost=cost, arm_id=arm_id, min_cost=min_cost, min_arm_id=min_arm_id)
				min_cost = cost
				min_arm_id = arm_id

		return min_arm_id

class Client_UCB():
	def __init__(self, _id, env, num_req_to_finish, win_len, inter_gen_time_rv, serv_time_rv, cl_l, out=None):
		self._id = _id
		self.env = env
		self.num_req_to_finish = num_req_to_finish
		self.inter_gen_time_rv = inter_gen_time_rv
		self.serv_time_rv = serv_time_rv
		self.cl_l = cl_l
		self.out = out

		cl_id_l = [cl._id for cl in cl_l]
		if win_len == 0:
			self.ucb = UCB_resetWindowOnRareEvent(cl_id_l)
		elif win_len < 0:
			win_len = abs(win_len)
			self.ucb = UCB_slidingWin(cl_id_l, win_len=len(cl_l)*win_len)
		else:
			self.ucb = UCB_slidingWinAtEachArm(cl_id_l, win_len)

		self.num_req_gened = 0
		self.num_req_finished = 0

		self.req_finished_l = []

		self.msg_s = simpy.Store(env)
		self.act_recv = env.process(self.run_recv())
		self.act_send = env.process(self.run_send())

	def __repr__(self):
		return 'Client_UCB(id= {})'.format(self._id)

	def set_out(self, out):
		self.out = out

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)
		self.msg_s.put(msg)

	def run_recv(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "handling", msg=msg)
			check(msg.payload.is_result(), "Msg should contain a result")
			res = msg.payload
			check(res.cid == self._id, "result.cid should equal to cid", result=res, cid=self._id)

			## Book keeping
			slog(DEBUG, self.env, self, "started book keeping", msg=msg)
			t = self.env.now
			res.epoch_arrived_client = t
			self.req_finished_l.append(res)

			response_time = res.epoch_arrived_client - res.epoch_departed_client
			check(response_time > 0, "Responsed time cannot be negative", response_time=response_time)
			self.ucb.record_cost(arm_id=res.cl_id, cost=response_time)

			slog(DEBUG, self.env, self, "",
					response_time = (res.epoch_arrived_client - res.epoch_departed_client),
					time_from_c_to_s = (res.epoch_arrived_cluster - res.epoch_departed_client),
					time_from_s_to_c = (res.epoch_arrived_client - res.epoch_departed_cluster),
					time_from_s_to_w_to_s = res.serv_time,
					result=res)

			self.num_req_finished += 1
			slog(DEBUG, self.env, self, "", num_req_gened=self.num_req_gened, num_req_finished=self.num_req_finished)

			slog(DEBUG, self.env, self, "done", msg_id=msg._id)
			if self.num_req_finished >= self.num_req_to_finish:
				break
		slog(DEBUG, self.env, self, "done")

	def run_send(self):
		while True:
			self.num_req_gened += 1
			req = Request(_id=self.num_req_gened, cid=self._id, serv_time=self.serv_time_rv.sample())
			req.epoch_departed_client = self.env.now
			msg = Msg(_id=self.num_req_gened, payload=req)

			## Send message
			to_cl_id = self.ucb.sample_arm()
			log(DEBUG, "to_cl_id= {}".format(to_cl_id))
			msg.payload.probe = False
			msg.payload.cl_id = to_cl_id
			msg.src_id = self._id
			msg.dst_id = to_cl_id
			self.out.put(msg)
			slog(DEBUG, self.env, self, "sent", req=req)

			inter_gen_time = self.inter_gen_time_rv.sample()
			slog(DEBUG, self.env, self, "sleeping", inter_gen_time=inter_gen_time)
			yield self.env.timeout(inter_gen_time)

		slog(DEBUG, self.env, self, "done")
