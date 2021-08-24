import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy, random

from msg import *
from debug_utils import *

class Client_RR():
	def __init__(self, _id, env, num_req_to_finish, inter_gen_time_rv, serv_time_rv, cl_l, out=None):
		self._id = _id
		self.env = env
		self.num_req_to_finish = num_req_to_finish
		self.inter_gen_time_rv = inter_gen_time_rv
		self.serv_time_rv = serv_time_rv
		self.cl_l = cl_l
		self.out = out

		self.cur_i = random.randint(0, len(cl_l) - 1)

		self.num_req_gened = 0
		self.num_req_finished = 0

		self.req_finished_l = []

		self.msg_s = simpy.Store(env)
		self.act_recv = env.process(self.run_recv())
		self.act_send = env.process(self.run_send())

	# def __repr__(self):
	# 	return 'Client_RR(' + '\n\t' + \
	# 		'id= {}'.format(self._id) + '\n\t' + \
	# 		'cl_l= {}'.format(self.cl_l) + '\n\t' + \
	# 		'num_req_to_finish= {}'.format(self.num_req_to_finish) + '\n\t' + \
	# 		'inter_gen_time_rv= {}'.format(self.inter_gen_time_rv) + '\n\t' + \
	# 		'serv_time_rv= {}'.format(self.serv_time_rv) + ')'

	def __repr__(self):
		return 'Client_RR(id= {})'.format(self._id)

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

			T = res.epoch_arrived_client - res.epoch_departed_client
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

	def run_send(self):
		while True:
			self.num_req_gened += 1
			req = Request(_id=self.num_req_gened, cid=self._id, serv_time=self.serv_time_rv.sample())
			req.epoch_departed_client = self.env.now
			msg = Msg(_id=self.num_req_gened, payload=req)

			## Send message
			msg.payload.probe = False
			msg.payload.cl_id = self.cl_l[self.cur_i]._id
			self.cur_i = (self.cur_i + 1) % len(self.cl_l)
			msg.src_id = self._id
			msg.dst_id = msg.payload.cl_id
			self.out.put(msg)
			slog(DEBUG, self.env, self, "sent", req=req)

			inter_gen_time = self.inter_gen_time_rv.sample()
			slog(DEBUG, self.env, self, "sleeping", inter_gen_time=inter_gen_time)
			yield self.env.timeout(inter_gen_time)

		slog(DEBUG, self.env, self, "done")
