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

		self.req_s = simpy.Store(env)

	def __repr__(self):
		return "Net(id= {})".format(self._id)

	def put(self, req):
		slog(DEBUG, self.env, self, "recved", req=req)
		req.epoch_arrived_net = self.env.now
		self.req_s.put(req)

class Net_wConstantDelay(Net):
	def __init__(self, _id, env, node_l, delay):
		super().__init__(_id, env, node_l)
		self.delay = delay

		self.action = env.process(self.run())

	def run(self):
		while True:
			req = yield self.req_s.get()

			t = self.delay - (self.env.now - req.epoch_arrived_net)
			if t > 0:
				slog(DEBUG, self.env, self, "delaying", req=req, t=t)
				yield self.env.timeout(t)

			self.id_out_m[req.dst_id].put(req)

class Cluster():
	def __init__(self, _id, env, num_worker, out=None):
		self._id = _id
		self.env = env
		self.num_worker = num_worker
		self.out = out

		w_l = [Worker('{}-w{}'.format(_id, i), env, self.out) for i in range(num_worker)]
		self.master = Master(_id, env, w_l)

	def __repr__(self):
		return "Cluster(id= {})".format(self._id)

	def set_out(self, out):
		self.master.set_out(out)

	def put(self, msg):
		log(DEBUG, "recved", msg=msg)
		self.master.put(msg)
