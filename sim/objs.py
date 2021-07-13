import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import random, simpy

from debug_utils import *
from rvs import *

class Cluster_wMarkovState():
	def __init__(self, env, _id, state_state_rate_m):
		self.env = env
		self._id = _id
		# {s1 : {s2: rate2}, {s3: rate3}}
		self.state_state_rate_m = state_state_rate_m

		self.cur_state = random.choice([s for s in state_state_rate_m])
		self.act = None

	# def __repr__(self):
	# 	return "Cluster_wMarkovState(" + "\n" \
	# 		     "id= {}".format(self._id) + "\n" + \
	# 				 "state_state_rate_m= \n{}".format(pprint.pformat(self.state_state_rate_m)) + ")"
	def __repr__(self):
		return "Cluster_wMarkovState(id= {})".format(self._id)

	def get_cur_state(self):
		return self.cur_state

	def start(self):
		self.act = self.env.process(self.run())
		slog(DEBUG, self.env, self, "started")

	def run(self):
		while True:
			total_rate = 0
			for to_state, rate in self.state_state_rate_m[self.cur_state].items():
				total_rate += rate

			rv = Exp(mu=total_rate)
			time = rv.sample()
			slog(DEBUG, self.env, self, "waiting", time=time, cur_state=self.cur_state)
			yield self.env.timeout(time)
			slog(DEBUG, self.env, self, "done waiting")

class Probe_iidClusters_wPodC():
	def __init__(self, env, num_cluster, state_state_rate_m, state_cost_m, d, inter_probe_time_rv, num_probe):
		self.env = env
		self.num_cluster = num_cluster
		self.state_state_rate_m = state_state_rate_m
		self.state_cost_m = state_cost_m
		self.d = d # number of clusters to probe at once
		self.inter_probe_time_rv = inter_probe_time_rv
		self.num_probe = num_probe

		self.cl_l = [Cluster_wMarkovState(env, 'cl_{}'.format(i), state_state_rate_m) for i in range(num_cluster)]

		self.epoch_started = None
		self.epoch_last_probed = None
		self.cost_l = []
		self.wait = env.process(self.run())

	def __repr__(self):
		return "Probe_iidClusters_wPodC(d= {})".format(self.d)

	def get_cost_per_unit_time(self):
		if self.epoch_last_probed == self.epoch_started:
			return None
		return sum(self.cost_l) / (self.epoch_last_probed - self.epoch_started)

	def run(self):
		for cl in self.cl_l:
			cl.start()
		slog(DEBUG, self.env, self, "all clusters started")

		self.epoch_started = self.env.now
		cur_cost = None

		# for i in range(self.num_probe):
		i = 0
		while True:
			i += 1
			slog(DEBUG, self.env, self, "{}the probe started".format(i))

			if self.epoch_last_probed is not None:
				self.cost_l.append((self.env.now - self.epoch_last_probed) * cur_cost)

			cl_to_probe_l = random.sample(self.cl_l, self.d)
			probed_state_l = [cl.get_cur_state() for cl in cl_to_probe_l]
			cur_cost = min(self.state_cost_m[state] for state in probed_state_l)
			self.epoch_last_probed = self.env.now
			slog(DEBUG, self.env, self, "probed", probed_state_l=probed_state_l, cur_cost=cur_cost)

			time = self.inter_probe_time_rv.sample()
			slog(DEBUG, self.env, self, "waiting before probing again", time=time)
			yield self.env.timeout(time)

		log(DEBUG, "done")
