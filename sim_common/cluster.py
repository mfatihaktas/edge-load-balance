import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import random
from collections import deque

from worker import *
from master import *
from debug_utils import *

class Net():
	def __init__(self, _id, env, node_l):
		self._id = _id
		self.env = env

		self.id_out_m = {}
		for n in node_l:
			n.set_out(self)
			self.id_out_m[n._id] = n

		self.msg_s = simpy.Store(env)
		self.act = env.process(self.run())

	def __repr__(self):
		return "Net(id= {})".format(self._id)

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)
		msg.epoch_arrived_net = self.env.now
		self.msg_s.put(msg)

	def run(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "forwarding", msg=msg)

			check(msg.dst_id in self.id_out_m, "Msg arrived for an unreged destination", msg_dst_id=msg.dst_id, id_out_m=self.id_out_m)
			self.id_out_m[msg.dst_id].put(msg)

class Cluster():
	def __init__(self, _id, env, num_worker, speed=1, slowdown=1, normal_dur_rv=None, slow_dur_rv=None, ignore_probe_cost=True, out=None):
		self._id = _id
		self.env = env
		self.num_worker = num_worker
		self.out = out

		if ignore_probe_cost:
			if slowdown > 1:
				# Worker_probesWaitBehindEachOther_fluctuatingSpeed
				self.w_l = [Worker_probesOnlyWaitBehindActualReqs_fluctuatingSpeed('{}-w{}'.format(_id, i), env, speed, slowdown, normal_dur_rv, slow_dur_rv, self.out) for i in range(num_worker)]
			else:
				# Worker_probesWaitBehindEachOther
				self.w_l = [Worker_probesOnlyWaitBehindActualReqs('{}-w{}'.format(_id, i), env, speed, self.out) for i in range(num_worker)]
		else:
			self.w_l = [Worker_probesTreatedAsActualReq('{}-w{}'.format(_id, i), env, speed, self.out) for i in range(num_worker)]

		self.master = Master(_id, env, self.w_l)

	def __repr__(self):
		return "Cluster(id= {})".format(self._id)

	def set_out(self, out):
		self.master.set_out(out)

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)
		self.master.put(msg)

	def min_wait_time(self):
		return min(w.min_wait_time() for w in self.w_l)
