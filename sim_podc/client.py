import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import numpy as np
import simpy, random
from collections import deque

from msg import *
from debug_utils import *

class InterProbeNumReq_controller_constant():
	def __init__(self, num):
		self.num = num

	def __repr__(self):
		return "InterProbeNumReq_controller_constant(num= {})".format(self.num)

	def update(self, T):
		pass

	def get_num(self):
		return self.num

class InterProbeNumReq_controller_learningWConstInc():
	def __init__(self, num, inc):
		self.num = num
		self.inc = inc

		self.ET_prev = None
		self.T_cur_l = []
		self.num_l = []

	def __repr__(self):
		return "InterProbeNumReq_controller_learningWConstInc(num= {}, inc= {})".format(self.num, self.inc)

	def update(self, T):
		log(DEBUG, "started", T=T)
		self.T_cur_l.append(T)

	def get_num(self):
		if self.ET_prev is None and len(self.T_cur_l) != 0:
			self.ET_prev = np.mean(self.T_cur_l)
		elif self.ET_prev is not None:
			ET_cur = np.mean(self.T_cur_l)

			log(DEBUG, "", ET_prev=self.ET_prev, ET_cur=ET_cur)
			if ET_cur < self.ET_prev * 0.9:
				self.num -= 1
				if self.num < 1:
					self.num = 2
			else:
				self.num += 1

			self.ET_prev = ET_cur
			self.T_cur_l.clear()

		self.num_l.append(self.num)
		return self.num

class Client_PodC():
	def __init__(self, _id, env, d, interProbeNumReq_controller,
							 num_req_to_finish, inter_gen_time_rv, serv_time_rv, cl_l,
							 initial_cl_id=None, out=None):
		self._id = _id
		self.env = env
		self.d = d
		self.interProbeNumReq_controller = interProbeNumReq_controller
		self.num_req_to_finish = num_req_to_finish
		self.inter_gen_time_rv = inter_gen_time_rv
		self.serv_time_rv = serv_time_rv
		self.cl_l = cl_l
		self.out = out

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
	# 		'interProbeNumReq_controller= {}'.format(self.interProbeNumReq_controller) + '\n\t' + \
	# 		'cl_l= {}'.format(self.cl_l) + '\n\t' + \
	# 		'num_req_to_finish= {}'.format(self.num_req_to_finish) + '\n\t' + \
	# 		'inter_gen_time_rv= {}'.format(self.inter_gen_time_rv) + '\n\t' + \
	# 		'serv_time_rv= {}'.format(self.serv_time_rv) + ')'

	def __repr__(self):
		return 'Client_PodC(id= {})'.format(self._id)

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

			T = res.epoch_arrived_client - res.epoch_departed_client
			self.interProbeNumReq_controller.update(T)

			slog(DEBUG, self.env, self, "",
					response_time = T,
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

	def replicate(self, cl_l, msg):
		slog(DEBUG, self.env, self, "started", cl_l=cl_l, msg=msg)
		for cl in cl_l:
			msg_ = msg.copy()
			msg_.dst_id = cl._id
			msg_.payload.cl_id = cl._id
			self.out.put(msg_)
			slog(DEBUG, self.env, self, "sent", cl_id=cl._id)
		slog(DEBUG, self.env, self, "done")

	def probe(self, msg):
		inter_probe_num_req = self.interProbeNumReq_controller.get_num()
		if self.d > 0 and self.waiting_for_probe == False and \
				 (self.num_req_gened == 1 or \
					self.num_req_gened - self.num_req_last_probed >= inter_probe_num_req):
			slog(DEBUG, self.env, self, "started", msg_id=msg._id)

			self.waiting_for_probe = True
			msg.payload.probe = True
			# cl_id_l = [cl._id for cl in self.cl_l if cl._id != self.assigned_cl_id]
			# cl_id_l = [self.assigned_cl_id, *random.sample(cl_id_l, self.d - 1)]
			cl_l = random.sample(self.cl_l, self.d)
			self.replicate(cl_l, msg)

			slog(DEBUG, self.env, self, "done", msg_id=msg._id)

	def run_send(self):
		while True:
			self.num_req_gened += 1
			req = Request(_id=self.num_req_gened, cid=self._id, serv_time=self.serv_time_rv.sample())
			req.epoch_departed_client = self.env.now
			msg = Msg(_id=self.num_req_gened, payload=req)

			## Send message to currently assigned cluster
			msg.payload.probe = False
			msg.payload.cl_id = self.assigned_cl_id
			msg.src_id = self._id
			msg.dst_id = self.assigned_cl_id
			self.out.put(msg)
			slog(DEBUG, self.env, self, "sent", req=req)

			## Send also its probe version if need to
			self.probe(msg)

			inter_gen_time = self.inter_gen_time_rv.sample()
			slog(DEBUG, self.env, self, "sleeping", inter_gen_time=inter_gen_time)
			yield self.env.timeout(inter_gen_time)

		slog(DEBUG, self.env, self, "done")
