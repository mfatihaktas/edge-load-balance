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

	def __repr__(self):
		return "Net(id= {})".format(self._id)

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)
		msg.epoch_arrived_net = self.env.now
		self.msg_s.put(msg)

## TODO: The following does not really incur constant delay on every request
class Net_wConstantDelay(Net):
	def __init__(self, _id, env, node_l, delay):
		super().__init__(_id, env, node_l)
		self.delay = delay

		self.act = env.process(self.run())

	def run(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "forwarding", msg=msg)

			t = self.delay - (self.env.now - msg.epoch_arrived_net)
			if t > 0:
				slog(DEBUG, self.env, self, "delaying", msg=msg, t=t)
				yield self.env.timeout(t)

			self.id_out_m[msg.dst_id].put(msg)

class FluctuatingState():
	def __init__(self, env, normal_dur_rv, slow_dur_rv):
		self.env = env
		self.normal_dur_rv = normal_dur_rv
		self.slow_dur_rv = slow_dur_rv

		self.state = 'n'

		self.act = env.process(self.run())

	def __repr__(self):
		return "FluctuatingState({})".format(self.state)

	def is_slow(self):
		return self.state == 's'

	def run(self):
		while True:
			if self.state == 'n':
				dur = self.normal_dur_rv.sample()
				slog(DEBUG, self.env, self, "will be normal", dur=dur)
				yield self.env.timeout(dur)

				self.state = 's'
			elif self.state == 's': # slow
				dur = self.slow_dur_rv.sample()
				slog(DEBUG, self.env, self, "will be slow", dur=dur)
				yield self.env.timeout(dur)

				self.state = 'n'
			else:
				assert_("Unexpected state", state=self.state)

class Net_wFluctuatingDelay(Net):
	def __init__(self, _id, env, node_l, delay, delay_additional, normal_dur_rv, slow_dur_rv):
		super().__init__(_id, env, node_l)
		self.delay = delay
		self.delay_additional = delay_additional
		self.normal_dur_rv = normal_dur_rv
		self.slow_dur_rv = slow_dur_rv

		self.dst_id__state_m = {}

		self.act = env.process(self.run())

	def reg_as_fluctuating(self, node_l):
		for node in node_l:
			self.dst_id__state_m[node._id] = FluctuatingState(self.env, self.normal_dur_rv, self.slow_dur_rv)
		log(DEBUG, "reged", dst_id__state_m=self.dst_id__state_m)

	def run(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "forwarding", msg=msg)

			t = self.delay - (self.env.now - msg.epoch_arrived_net)
			check(t >= 0, "Net delay minus the time spent in the net cannot be negative")
			if t > 0:
				slog(DEBUG, self.env, self, "delaying", msg=msg, t=t)
				yield self.env.timeout(t)

			dst_id = msg.dst_id
			if dst_id in self.dst_id__state_m:
				state = self.dst_id__state_m[dst_id]
				if state.is_slow():
					slog(DEBUG, self.env, self, "delaying additional", msg=msg, delay_additional=self.delay_additional)
					yield self.env.timeout(self.delay_additional)

			self.id_out_m[dst_id].put(msg)

## !!!: The following does not work
class Net_FCFS():
	def __init__(self, _id, env, node_l, speed):
		self._id = _id
		self.env = env
		self.speed = speed

		self.dst_id__state_m = None

		self.act_l = []
		for n in node_l:
			n.set_out(self)
			self.act_l.append(env.process(self.run(n)))

		self.msg_s = simpy.Store(env)

	def __repr__(self):
		return "Net_FCFS(id= {})".format(self._id)

	def reg_as_fluctuating(self, node_l, slowdown, normal_dur_rv, slow_dur_rv):
		self.dst_id__state_m = {}
		for node in node_l:
			self.dst_id__state_m[node._id] = FluctuatingState(self.env, self.normal_dur_rv, self.slow_dur_rv)
		log(DEBUG, "reged", dst_id__state_m=self.dst_id__state_m)

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)
		msg.epoch_arrived_net = self.env.now
		self.msg_s.put(msg)

	def run(self, node):
		log(DEBUG, "started", node=node)

		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "forwarding", msg=msg)

			dst_id = msg.dst_id
			check(dst_id == node._id, 'Msg dst_id should match with the node id')

			speed = self.speed
			if self.dst_id__state_m is not None and dst_id in self.dst_id__state_m:
				state = self.dst_id__state_m[dst_id]
				if state.is_slow():
					slog(DEBUG, self.env, self, "slow", msg_dst_id=msg.dst_id)
					speed /= self.slowdown

			t = msg.size / speed
			slog(DEBUG, self.env, self, "serving", t=t)
			yield self.env.timeout(t)

			node.put(msg)

class Cluster():
	def __init__(self, _id, env, num_worker, ignore_probe_cost=True, out=None):
		self._id = _id
		self.env = env
		self.num_worker = num_worker
		self.out = out

		if ignore_probe_cost:
			w_l = [Worker('{}-w{}'.format(_id, i), env, self.out) for i in range(num_worker)]
		else:
			w_l = [Worker_probesTreatedAsActualReq('{}-w{}'.format(_id, i), env, self.out) for i in range(num_worker)]

		self.master = Master(_id, env, w_l)

	def __repr__(self):
		return "Cluster(id= {})".format(self._id)

	def set_out(self, out):
		self.master.set_out(out)

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)
		self.master.put(msg)
