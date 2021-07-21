import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy

from msg import result_from_req, InfoType, Info
from debug_utils import *

class Worker():
	def __init__(self, _id, env, out=None):
		self._id = _id
		self.env = env
		self.out = out

		self.master = None

		self.msg_s = simpy.Store(env)

		self.msg_to_send_s = simpy.Store(env)
		self.act_send = env.process(self.run_send())

		self.probe_to_send_s = simpy.Store(env)
		self.act_probe = env.process(self.run_send_probe())

		self.act = env.process(self.run())

	def reg_master(self, master):
		self.master = master

	def put(self, msg):
		check(msg.payload.is_req(), "Msg should contain a request")
		self.msg_s.put(msg)

	def run(self):
		while True:
			msg = yield self.msg_s.get()

			req = msg.payload
			if not req.probe:
				slog(DEBUG, self.env, self, "serving", serv_time=req.serv_time)
				yield self.env.timeout(req.serv_time)
				slog(DEBUG, self.env, self, "finished serving")

			## Send to master
			msg.payload = Info(req._id, InfoType.worker_req_completion)
			msg.dst_id = msg.src_id
			msg.src_id = self._id
			self.master.put(msg)

			res = result_from_req(req)
			res.epoch_departed_cluster = self.env.now
			msg.payload = res

			if req.probe:
				self.probe_to_send_s.put(msg)
			else:
				self.msg_to_send_s.put(msg)

		slog(DEBUG, self.env, self, "done")

	def run_send_probe(self):
		while True:
			msg = yield self.probe_to_send_s.get()

			serv_time = msg.payload.serv_time
			log(DEBUG, "sleeping for probe", serv_time=serv_time)
			yield self.env.timeout(serv_time)
			log(DEBUG, "done sleeping for probe")

			self.msg_to_send_s.put(msg)

	def run_send(self):
		while True:
			msg = yield self.msg_to_send_s.get()

			## Send to client
			msg.src_id = self._id
			msg.dst_id = msg.payload.cid
			self.out.put(msg)
