import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import random
from collections import deque

from debug_utils import *

class Request():
	def __init__(self, _id, src_id, dst_id, serv_time):
		self._id = _id
		self.src_id = src_id
		self.dst_id = dst_id
		self.serv_time = serv_time

		self.epoch_departed_client = None
		self.epoch_arrived_net = None
		self.epoch_arrived_cluster = None
		self.epoch_started_service = None
		self.epoch_departed_cluster = None
		self.epoch_arrived_client = None

		self.num_server_share = None

	def __repr__(self):
		return "Request(id= {}, src_id= {}, dst_id= {}, serv_time= {})".format(self._id, self.src_id, self.dst_id, self.serv_time)

class Msg():
	def __init__(self, _id, payload, src_id=None, dst_id=None):
		self._id = _id
		self.payload = payload
		self.src_id = src_id
		self.dst_id = dst_id

	def __repr__(self):
		return "Msg(id= {} \n\t payload= {} \n\t src_id= {} \n\t dst_id= {})".format(self._id, self.payload, self.src_id, self.dst_id)

class Payload():
	def __init__(self, _id, p_typ):
		self._id = _id
		self.p_typ = p_typ

	def is_req(self):
		return self.p_typ == 'r'

	def is_result(self):
		return self.p_typ == 's'

	def is_info(self):
		return self.p_typ == 'i'

	def is_update(self):
		return self.p_typ == 'u'

class InfoType(enum.Enum):
	client_disconn = 1
	worker_req_completion = 2

class Info(Payload):
	def __init__(self, _id, typ: InfoType):
		super().__init__(_id, 'i')
		self.typ = typ

	def __repr__(self):
		return "Info(typ= {})".format(self.typ.name)

class ReqRes(Payload):
	def __init__(self, _id, p_typ, cid, serv_time=None, probe=False):
		super().__init__(_id, p_typ)
		self.cid = cid
		self.serv_time = serv_time
		self.probe = probe

		self.cl_id = None
		self.epoch_departed_client = None
		self.epoch_arrived_cluster = None
		self.epoch_departed_cluster = None
		self.epoch_arrived_client = None

	def __hash__(self):
		return hash((self._id, self.cid))

	def __eq__(self, other):
		return (self._id, self.cid) == (other._id, other.cid)

class Request(ReqRes):
	def __init__(self, _id, cid, serv_time):
		super().__init__(_id, 'r', cid, serv_time)

	def __repr__(self):
		return "Request(id= {}, cid= {}, cl_id= {}, serv_time= {}, probe= {})".format(self._id, self.cid, self.cl_id, self.serv_time, self.probe)

class Result(ReqRes):
	def __init__(self, _id, cid):
		super().__init__(_id, 's', cid)

	def __repr__(self):
		return "Result(id= {}, cid= {}, cl_id= {}, probe= {})".format(self._id, self.cid, self.cl_id, self.probe)

def result_from_req(req):
	r = Result(req._id, req.cid, req.cip)

	r.cl_id = req.cl_id
	r.serv_time = req.serv_time
	r.probe = req.probe
	r.epoch_departed_client = req.epoch_departed_client
	r.epoch_arrived_cluster = req.epoch_arrived_cluster
	r.epoch_departed_cluster = req.epoch_departed_cluster
	r.epoch_arrived_client = req.epoch_arrived_client
	return r

class Client():
	def __init__(self, _id, env, d, inter_probe_num_reqs, cl_l,
							 num_req_to_finish, inter_gen_time_rv, serv_time_rv, out):
		self._id = _id
		self.env = env
		self.d = d
		self.inter_probe_num_reqs = inter_probe_num_reqs
		self.cl_l = cl_l
		self.num_req_to_finish = num_req_to_finish
		self.inter_gen_time_rv = inter_gen_time_rv
		self.serv_time_rv = serv_time_rv
		self.out = out

		self.inter_probe_num_reqs_ = self.inter_probe_num_reqs

		self.num_reqs_gened = 0
		self.num_reqs_finished = 0
		self.num_reqs_last_probed = 0

		self.req_finished_l = []

		self.assigned_cl_id = random.randint(0, len(cl_l))
		self.waiting_for_probe = False

		self.msg_s = simpy.Store(env)
		self.act_recv = env.process(self.run_recv())
		self.act_send = env.process(self.run_send())

	def __repr__(self):
		return 'Client(' + '\n\t' + \
			'id= {}'.format(self._id) + '\n\t' + \
			'inter_probe_num_reqs= {}'.format(self.inter_probe_num_reqs) + '\n\t' + \
			'cl_l= {}'.format(self.cl_l) + '\n\t' + \
			'num_reqs_to_finish= {}'.format(self.num_reqs_to_finish) + '\n\t' + \
			'inter_gen_time_rv= {}'.format(self.inter_gen_time_rv) + '\n\t' + \
			'serv_time_rv= {}'.format(self.serv_time_rv) + ')'

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)
		self.msg_s.put(msg)

	def run_recv(self):
		while True:
			msg = yield self.msg_s.get()
			slog(DEBUG, self.env, self, "handling", msg=msg)
			check(msg.payload.is_result(), "Msg should contain a result")
			result = msg.payload
			check(result.cid == self._id, "result.cid should equal to cid", result=result, cid=self._id)

			if result.probe:
				if self.waiting_for_probe:
					if self.assigned_cl_id != result.src_id:
						msg_ = Msg(0, payload=Info(0, InfoType.client_disconn), src_id=self._id, dst_id=msg.src_id)
						self.out.put(msg_)

					self.assigned_cl_id = msg.src_id
					self.num_reqs_last_probed = self.num_reqs_gened
					self.waiting_for_probe = False
					slog(DEBUG, self.env, self, "Set assigned_cl_id", assigned_cl_id=self.assigned_cl_id)
				else:
					slog(DEBUG, self.env, self, "Late probe result has been recved", msg=msg)
				continue

			## Book keeping
			slog(DEBUG, self.env, self, "started book keeping", msg=msg)
			t = self.env.now
			result.epoch_arrived_client = t
			self.req_finished_l.append(result)

			slog(DEBUG, self.env, self, "",
					response_time = (result.epoch_arrived_client - result.epoch_departed_client),
					time_from_c_to_s = (result.epoch_arrived_cluster - result.epoch_departed_client),
					time_from_s_to_c = (result.epoch_arrived_client - result.epoch_departed_cluster),
					time_from_s_to_w_to_s = result.serv_time,
					result=result)

			self.num_reqs_finished += 1
			slog(DEBUG, self.env, self, "", num_reqs_gened=self.num_reqs_gened, num_reqs_finished=self.num_reqs_finished)

			slog(DEBUG, self.env, self, "done", msg_id=msg._id)
			if self.num_reqs_finished >= self.num_reqs_to_finish:
				break
		slog(DEBUG, self.env, self, "done")

	def replicate(self, cl_id_l, msg):
		slog(DEBUG, self.env, self, "started", cl_id_l=cl_id_l, msg=msg)
		for cl_id in cl_id_l:
			msg.dst_id = cl_id
			self.out.put(msg)
			slog(DEBUG, self.env, self, "sent", cl_id=cl_id)
		slog(DEBUG, self.env, self, "done")

	def probe(self, msg):
		if self.d > 1 and self.waiting_for_probe == False and \
				 (self.num_reqs_gened == 1 or \
					self.num_reqs_gened - self.num_reqs_last_probed >= self.inter_probe_num_reqs_):
			slog(DEBUG, self.env, self, "started", msg_id=msg._id)

			msg.payload.probe = True
			self.waiting_for_probe = True
			cl_id_l = [i for i in range(len(self.cl_l)) if i != self.assigned_cl_id]
			cl_id_l = [self.assigned_cl_id, *random.sample(self.cl_id_l, self.d - 1)]
			slog(DEBUG, self.env, self, "will probe", cl_id_l=cl_id_l)

			self.replicate(cl_id_l, msg)
			step = int(self.inter_probe_num_reqs * 0.4)
			self.inter_probe_num_reqs_ = self.inter_probe_num_reqs + random.randrange(-step, step + 1)

			slog(DEBUG, self.env, self, "done", msg_id=msg._id)

	def run_send(self):
		while True:
			self.num_reqs_gened += 1
			req = Request(_id=self.num_reqs_gened, cid=self._id, serv_time=self.serv_time_rv.sample())
			req.epoch_departed_client = self.env.now
			msg = Msg(_id=self.num_reqs_gened, payload=req)

			## Send also its probe version if need to
			self.probe(msg)

			## Send message to currently assigned master
			msg.payload.probe = False
			msg.dst_id = self.assigned_cl_id
			self.out.put(msg)
			slog(DEBUG, self.env, self, "sent", req=req)

			inter_gen_time = self.inter_gen_time_rv.sample()
			slog(DEBUG, self.env, self, "sleeping", inter_gen_time=inter_gen_time)
			yield self.env.timeout(inter_gen_time)

		slog(DEBUG, self.env, self, "done")

class Worker():
	def __init__(self, _id, env, slowdown_rv, out=None):
		self._id = _id
		self.env = env
		self.slowdown_rv = slowdown_rv
		self.out = out

		self.req_s = simpy.Store(env)
		self.action = env.process(self.run())
		self.is_serving = False

	def __repr__(self):
		return "Worker(_id= {})".format(self._id)

	def put(self, req):
		slog(DEBUG, self.env, self, "recved", req=req)
		self.req_s.put(req)

	def num_reqs(self):
		return len(self.req_s.items) + int(self.is_serving)

	def run(self):
		while True:
			req = yield self.req_s.get()
			req.epoch_started_service = self.env.now

			self.is_serving = True
			s = self.slowdown_rv.sample()
			t = s * req.serv_time
			slog(DEBUG, self.env, self, "started serving", slowdown=s, req=req, t=t)
			yield self.env.timeout(t)
			slog(DEBUG, self.env, self, "finished serving", req_id=req._id)

			req.serv_time = t
			self.is_serving = False
			self.out.put_result(self._id, req)

class Cluster():
	def __init__(self, _id, env, slowdown_rv, num_server, out=None):
		self._id = _id
		self.env = env
		self.num_server = num_server
		self.out = out

		self.cid_q_m = {}
		self.next_cid_to_pop_q = deque()
		self.server_l = [Worker(i, env, slowdown_rv, out=self) for i in range(num_server)]

		self.sid_s = simpy.Store(env)
		for i in range(num_server):
			self.sid_s.put(i)

		self.waiting_for_req = True
		self.syncer_s = simpy.Store(env)
		self.result_s = simpy.Store(env)

		self.action_handle_reqs = env.process(self.run_handle_reqs())
		self.action_handle_results = env.process(self.run_handle_results())

		self.epoch_nreqs_l = []

	def __repr__(self):
		return "Cluster(_id= {})".format(self._id)

	def reg(self, cid):
		if cid not in self.cid_q_m:
			self.cid_q_m[cid] = deque()
			self.next_cid_to_pop_q.append(cid)
			log(DEBUG, "reged", cid=cid)

	def num_reqs(self):
		return sum(len(q) for _, q in self.cid_q_m.items()) + sum(s.num_reqs() for s in self.server_l)

	def record_num_reqs(self):
		self.epoch_nreqs_l.append((self.env.now, self.num_reqs()))

	def put(self, req):
		slog(DEBUG, self.env, self, "recved", req=req)
		req.epoch_arrived_cluster = self.env.now

		if req.src_id not in self.cid_q_m:
			self.reg(req.src_id)
		self.cid_q_m[req.src_id].append(req)

		if self.waiting_for_req: # and len(self.syncer_s.items) == 0:
			self.syncer_s.put(1)

	def put_result(self, sid, result):
		slog(DEBUG, self.env, self, "recved", result=result)
		self.sid_s.put(sid)
		self.result_s.put(result)

	def next_req(self):
		for _ in range(len(self.cid_q_m)):
			q = self.cid_q_m[self.next_cid_to_pop_q[0]]
			self.next_cid_to_pop_q.rotate(-1)
			if len(q) > 0:
				return q.popleft()
		return None

	def run_handle_reqs(self):
		while True:
			sid = yield self.sid_s.get()

			req = self.next_req()
			if req is None:
				slog(DEBUG, self.env, self, "waiting for a req")
				self.waiting_for_req = True
				yield self.syncer_s.get()
				self.waiting_for_req = False
				slog(DEBUG, self.env, self, "recved a req")
				req = self.next_req()
				check(req is not None, "A req must have been recved")

			# req = self.next_req()
			# while req is None:
			# 	yield self.env.timeout(0.01)
			# 	req = self.next_req()

			self.server_l[sid].put(req)
			self.record_num_reqs()

	def run_handle_results(self):
		while True:
			result = yield self.result_s.get()
			result.src_id, result.dst_id = result.dst_id, result.src_id
			result.epoch_departed_cluster = self.env.now
			result.num_server_share = self.num_server / len(self.cid_q_m)
			self.out.put(result)

			self.record_num_reqs()

class Net():
	def __init__(self, _id, env, cs_l):
		self._id = _id
		self.env = env

		self.id_out_m = {}
		for cs in cs_l:
			cs.out = self
			self.id_out_m[cs._id] = cs

		self.req_s = simpy.Store(env)

	def __repr__(self):
		return "Net(id= {})".format(self._id)

	def put(self, req):
		slog(DEBUG, self.env, self, "recved", req=req)
		req.epoch_arrived_net = self.env.now
		self.req_s.put(req)

class Net_wConstantDelay(Net):
	def __init__(self, _id, env, cs_l, delay):
		super().__init__(_id, env, cs_l)
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
