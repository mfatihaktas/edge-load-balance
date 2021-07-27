import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy, random

from msg import *
from debug_utils import *

class Client():
	def __init__(self, _id, env, d, inter_probe_num_req,
							 num_req_to_finish, inter_gen_time_rv, serv_time_rv, cl_l,
							 initial_cl_id=None, out=None):
		self._id = _id
		self.env = env
		self.d = d
		self.inter_probe_num_req = inter_probe_num_req
		self.num_req_to_finish = num_req_to_finish
		self.inter_gen_time_rv = inter_gen_time_rv
		self.serv_time_rv = serv_time_rv
		self.cl_l = cl_l
		self.out = out

		self.inter_probe_num_req_ = self.inter_probe_num_req

		self.num_req_gened = 0
		self.num_req_finished = 0
		self.num_req_last_probed = 0

		self.req_finished_l = []

		self.assigned_cl_id = initial_cl_id if initial_cl_id is not None else random.sample(self.cl_l, 1)[0]._id
		self.waiting_for_probe = False

		self.msg_s = simpy.Store(env)
		self.act_recv = env.process(self.run_recv())
		self.act_send = env.process(self.run_send())

	# def __repr__(self):
	# 	return 'Client(' + '\n\t' + \
	# 		'id= {}'.format(self._id) + '\n\t' + \
	# 		'inter_probe_num_req= {}'.format(self.inter_probe_num_req) + '\n\t' + \
	# 		'cl_l= {}'.format(self.cl_l) + '\n\t' + \
	# 		'num_req_to_finish= {}'.format(self.num_req_to_finish) + '\n\t' + \
	# 		'inter_gen_time_rv= {}'.format(self.inter_gen_time_rv) + '\n\t' + \
	# 		'serv_time_rv= {}'.format(self.serv_time_rv) + ')'

	def __repr__(self):
		return 'Client(id= {})'.format(self._id)

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

			if res.probe:
				if self.waiting_for_probe:
					if self.assigned_cl_id != res.cl_id:
						msg_ = Msg(0, payload=Info(0, InfoType.client_disconn), src_id=self._id, dst_id=res.cl_id)
						self.out.put(msg_)

					self.assigned_cl_id = res.cl_id
					self.num_req_last_probed = self.num_req_gened
					self.waiting_for_probe = False
					slog(DEBUG, self.env, self, "Set assigned_cl_id", assigned_cl_id=self.assigned_cl_id)
				else:
					slog(DEBUG, self.env, self, "Late probe result has been recved", msg=msg)
				continue

			## Book keeping
			slog(DEBUG, self.env, self, "started book keeping", msg=msg)
			t = self.env.now
			res.epoch_arrived_client = t
			self.req_finished_l.append(res)

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

	def replicate(self, cl_id_l, msg):
		slog(DEBUG, self.env, self, "started", cl_id_l=cl_id_l, msg=msg)
		for cl_id in cl_id_l:
			msg_ = msg.copy()
			msg_.dst_id = cl_id
			msg_.payload.cl_id = cl_id
			self.out.put(msg_)
			slog(DEBUG, self.env, self, "sent", cl_id=cl_id)
		slog(DEBUG, self.env, self, "done")

	def probe(self, msg):
		if self.d > 1 and self.waiting_for_probe == False and \
				 (self.num_req_gened == 1 or \
					self.num_req_gened - self.num_req_last_probed >= self.inter_probe_num_req_):
			slog(DEBUG, self.env, self, "started", msg_id=msg._id)

			msg.payload.probe = True
			self.waiting_for_probe = True
			cl_id_l = [cl._id for cl in self.cl_l if cl._id != self.assigned_cl_id]
			cl_id_l = [self.assigned_cl_id, *random.sample(cl_id_l, self.d - 1)]
			slog(DEBUG, self.env, self, "will probe", cl_id_l=cl_id_l)

			self.replicate(cl_id_l, msg)
			step = int(self.inter_probe_num_req * 0.2)
			self.inter_probe_num_req_ = self.inter_probe_num_req + random.randrange(-step, step + 1)

			slog(DEBUG, self.env, self, "done", msg_id=msg._id)

	def run_send(self):
		while True:
			self.num_req_gened += 1
			req = Request(_id=self.num_req_gened, cid=self._id, serv_time=self.serv_time_rv.sample())
			req.epoch_departed_client = self.env.now
			msg = Msg(_id=self.num_req_gened, payload=req)

			## Send also its probe version if need to
			self.probe(msg)

			## Send message to currently assigned cluster
			msg.payload.probe = False
			msg.payload.cl_id = self.assigned_cl_id
			msg.src_id = self._id
			msg.dst_id = self.assigned_cl_id
			self.out.put(msg)
			slog(DEBUG, self.env, self, "sent", req=req)

			inter_gen_time = self.inter_gen_time_rv.sample()
			slog(DEBUG, self.env, self, "sleeping", inter_gen_time=inter_gen_time)
			yield self.env.timeout(inter_gen_time)

		slog(DEBUG, self.env, self, "done")
