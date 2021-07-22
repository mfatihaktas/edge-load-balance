import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy
from collections import deque

from msg import Msg, InfoType
from priority_dict import *
from debug_utils import *

class RRQueue(): # Round Robin
	def __init__(self, max_qlen):
		self.max_qlen = max_qlen

		self.cid_q_m = {}
		self.next_cid_to_pop_q = deque()

		self.num_dropped = 0

	def reg(self, cid):
		if cid not in self.cid_q_m:
			self.cid_q_m[cid] = deque()
			self.next_cid_to_pop_q.append(cid)
			log(DEBUG, "reged", cid=cid)

	def unreg(self, cid):
		if cid in self.cid_q_m:
			self.cid_q_m.pop(cid)
			self.next_cid_to_pop_q.remove(cid)
			log(DEBUG, "unreged", cid=cid)

	def push(self, msg):
		if msg.payload.cid not in self.cid_q_m:
			self.reg(msg.payload.cid)

		r = True
		q = self.cid_q_m[msg.payload.cid]
		if len(q) == self.max_qlen:
			# msg_popped = q.popleft()
			# log(DEBUG, "Was full, popped the oldest req", msg_popped=msg_popped)
			log(DEBUG, "Was full, dropped", msg=msg)
			self.num_dropped += 1
			r = False
		else:
			q.append(msg)
			log(DEBUG, "pushed", msg=msg)
		return r

	def pop(self):
		for _ in range(len(self.cid_q_m)):
			q = self.cid_q_m[self.next_cid_to_pop_q[0]]
			self.next_cid_to_pop_q.rotate(-1)
			if len(q) > 0:
				return q.popleft()
		return None

class WQueue(): # Worker
	def __init__(self, wid_s, w_token_s, max_qlen):
		self.w_token_s = w_token_s
		self.max_qlen = max_qlen

		self.wid_qlen_heap_m = priority_dict()
		for wid in wid_s:
			self.wid_qlen_heap_m[wid] = 0

			for _ in range(self.max_qlen):
				self.w_token_s.put(1)

		log(DEBUG, "WQueue constructed", wid_s=wid_s)

	def update(self, new_wid_s):
		log(DEBUG, "started", new_wid_s=new_wid_s)

		## Drop wid's that got removed
		for wid in [i for i in self.wid_qlen_heap_m]:
			if wid not in new_wid_s:
				qlen = self.wid_qlen_heap_m[wid]
				log(DEBUG, "dropping", wid=wid, qlen=qlen)
				for _ in range(self.max_qlen - qlen):
					yield self.w_token_s.get()

				self.wid_qlen_heap_m.pop(wid)
		## Add new wid's
		for wid in new_wid_s:
			if wid not in self.wid_qlen_heap_m:
				log(DEBUG, "adding", wid=wid)
				self.wid_qlen_heap_m[wid] = 0
				for _ in range(self.max_qlen):
					self.w_token_s.put(1)
		log(DEBUG, "done")

	def inc_qlen(self, wid):
		log(DEBUG, "started", wid=wid)
		self.wid_qlen_heap_m[wid] += 1
		check(self.wid_qlen_heap_m[wid] <= self.max_qlen, "Q-len cannot be greater than max_qlen= {}".format(self.max_qlen))
		log(DEBUG, "done", wid=wid, qlen=self.wid_qlen_heap_m[wid])

	def dec_qlen(self, wid):
		log(DEBUG, "started", wid=wid)
		try:
			self.wid_qlen_heap_m[wid] -= 1
		except KeyError:
			log(DEBUG, "tried on non-existent key", wid=wid)
			return
		check(self.wid_qlen_heap_m[wid] >= 0, "Q-len cannot be negative")

		self.w_token_s.put(1)
		log(DEBUG, "done", wid=wid, qlen=self.wid_qlen_heap_m[wid])

	def pop(self):
		wid = self.wid_qlen_heap_m.smallest()
		qlen = self.wid_qlen_heap_m[wid]

		if qlen >= self.max_qlen:
			log(WARNING, "Attempted to return a full worker", qlen=qlen)
			return None
		return wid

class Master():
	def __init__(self, _id, env, w_l):
		self._id = _id
		self.env = env

		self.id_w_m = {}
		for w in w_l:
			w.reg_master(self)
			self.id_w_m[w._id] = w

		self.msg_token_s = simpy.Store(env)
		self.msg_q = RRQueue(max_qlen=5)

		self.w_token_s = simpy.Store(env)
		self.w_q = WQueue([w._id for w in w_l], self.w_token_s, max_qlen=30)

		self.act = env.process(self.run())

	def __repr__(self):
		return "Master(id= {})".format(self._id)

	def set_out(self, out):
		for _, w in self.id_w_m.items():
			w.out = out

	def put(self, msg):
		slog(DEBUG, self.env, self, "recved", msg=msg)

		p = msg.payload
		if p.is_req():
			p.epoch_arrived_cluster = self.env.now
			if self.msg_q.push(msg):
				self.msg_token_s.put(1)
		elif p.is_info():
			if p.typ == InfoType.client_disconn:
				# TODO: uncomment the following
				# self.msg_q.unreg(msg.src_id)
				pass
			elif p.typ == InfoType.worker_req_completion:
				self.w_q.dec_qlen(msg.src_id)
		else:
			slog(ERROR, self.env, self, "Unexpected payload type", payload=p)

	def run(self):
		while True:
			slog(DEBUG, self.env, self, "Waiting for msg")
			yield self.msg_token_s.get()
			msg = self.msg_q.pop()
			check(msg is not None, "Msg must have arrived")

			slog(DEBUG, self.env, self, "Waiting for worker")
			yield self.w_token_s.get()
			slog(DEBUG, self.env, self, "", w_token_s_len=len(self.w_token_s.items))
			wid = self.w_q.pop()
			check(wid is not None, "There should have been an available worker")

			## Send to worker
			msg.src_id = self._id
			msg.dst_id = wid
			self.id_w_m[wid].put(msg)
			if msg.payload.is_req():
				slog(DEBUG, self.env, self, "Will inc_qlen", wid=wid)
				self.w_q.inc_qlen(wid)
