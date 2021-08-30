import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy

from msg import result_from_req, InfoType, Info
from debug_utils import *

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

class Worker_base():
	def __init__(self, _id, env, speed=1, out=None):
		self._id = _id
		self.env = env
		self.speed = speed
		self.out = out

		self.master = None

		self.msg_s = simpy.Store(env)
		self.msg_to_send_s = simpy.Store(env)
		self.act_send = self.env.process(self.run_send())

	def __repr__(self):
		return "Worker_base(id= {})".format(self._id)

	def reg_master(self, master):
		self.master = master

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)
		check(msg.payload.is_req(), "Msg should contain a request")
		self.msg_s.put(msg)

	def run_send(self):
		while True:
			msg = yield self.msg_to_send_s.get()

			## Send to client
			msg.src_id = self._id
			msg.dst_id = msg.payload.cid
			self.out.put(msg)

class Worker_probesWaitBehindEachOther(Worker_base):
	def __init__(self, _id, env, speed=1, out=None):
		super().__init__(_id, env, speed, out)

		self.probe_to_send_s = simpy.Store(env)
		self.act_probe = self.env.process(self.run_send_probe())

		self.act = env.process(self.run())

	def __repr__(self):
		return "Worker_probesWaitBehindEachOther(id= {})".format(self._id)

	def run_send_probe(self):
		while True:
			msg = yield self.probe_to_send_s.get()

			serv_time = msg.payload.serv_time
			slog(DEBUG, self.env, self, "sleeping for probe", serv_time=serv_time)
			yield self.env.timeout(serv_time)
			slog(DEBUG, self.env, self, "done sleeping for probe")

			self.msg_to_send_s.put(msg)

	def run(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "working on", msg=msg)

			req = msg.payload
			if not req.probe:
				t = req.serv_time / self.speed
				slog(DEBUG, self.env, self, "serving", t=t)
				yield self.env.timeout(t)
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

class Worker_probesWaitBehindEachOther_fluctuatingSpeed(Worker_base):
	def __init__(self, _id, env, speed, slowdown, normal_dur_rv, slow_dur_rv, out=None):
		super().__init__(_id, env, speed, out)
		self.slowdown = slowdown

		self.state = FluctuatingState(env, normal_dur_rv, slow_dur_rv)
		self.act = env.process(self.run())

	def __repr__(self):
		return "Worker_probesWaitBehindEachOther_fluctuatingSpeed(id= {})".format(self._id)

	def run(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "working on", msg=msg)

			req = msg.payload
			if not req.probe:
				speed = self.speed
				if self.state.is_slow():
					speed /= self.slowdown

				t = req.serv_time / speed
				slog(DEBUG, self.env, self, "serving", t=t)
				yield self.env.timeout(t)
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

class Worker_probesOnlyWaitBehindActualReqs(Worker_base):
	def __init__(self, _id, env, speed=1, out=None):
		super().__init__(_id, env, speed, out)

		self.act = env.process(self.run())

	def __repr__(self):
		return "Worker_probesOnlyWaitBehindActualReqs(id= {})".format(self._id)

	def run(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "working on", msg=msg)

			req = msg.payload
			if not req.probe:
				t = req.serv_time / self.speed
				slog(DEBUG, self.env, self, "serving", t=t)
				yield self.env.timeout(t)
				slog(DEBUG, self.env, self, "finished serving")

			## Send to master
			msg.payload = Info(req._id, InfoType.worker_req_completion)
			msg.dst_id = msg.src_id
			msg.src_id = self._id
			self.master.put(msg)

			res = result_from_req(req)
			res.epoch_departed_cluster = self.env.now
			msg.payload = res

			self.msg_to_send_s.put(msg)

		slog(DEBUG, self.env, self, "done")

class Worker_probesOnlyWaitBehindActualReqs_fluctuatingSpeed(Worker_base):
	def __init__(self, _id, env, speed, slowdown, normal_dur_rv, slow_dur_rv, out=None):
		super().__init__(_id, env, speed, out)
		self.slowdown = slowdown

		self.state = FluctuatingState(env, normal_dur_rv, slow_dur_rv)

		self.act = env.process(self.run())

	def __repr__(self):
		return "Worker_probesOnlyWaitBehindActualReqs_fluctuatingSpeed(id= {})".format(self._id)

	def run(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "working on", msg=msg)

			req = msg.payload
			if not req.probe:
				speed = self.speed
				if self.state.is_slow():
					speed /= self.slowdown

				t = req.serv_time / speed
				slog(DEBUG, self.env, self, "serving", t=t)
				yield self.env.timeout(t)
				slog(DEBUG, self.env, self, "finished serving")

			## Send to master
			msg.payload = Info(req._id, InfoType.worker_req_completion)
			msg.dst_id = msg.src_id
			msg.src_id = self._id
			self.master.put(msg)

			res = result_from_req(req)
			res.epoch_departed_cluster = self.env.now
			msg.payload = res

			self.msg_to_send_s.put(msg)

		slog(DEBUG, self.env, self, "done")

class Worker_probesTreatedAsActualReq(Worker_base):
	def __init__(self, _id, env, speed=1, out=None):
		super().__init__(_id, env, speed, out)

		self.act = env.process(self.run())

	def __repr__(self):
		return "Worker_probesTreatedAsActualReq(id= {})".format(self._id)

	def run(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "working on", msg=msg)

			req = msg.payload
			t = req.serv_time / self.speed
			slog(DEBUG, self.env, self, "serving", t=t)
			yield self.env.timeout(t)
			slog(DEBUG, self.env, self, "finished serving")

			## Send to master
			msg.payload = Info(req._id, InfoType.worker_req_completion)
			msg.dst_id = msg.src_id
			msg.src_id = self._id
			self.master.put(msg)

			res = result_from_req(req)
			res.epoch_departed_cluster = self.env.now
			msg.payload = res

			## Queue for sending to client
			self.msg_to_send_s.put(msg)

		slog(DEBUG, self.env, self, "done")
