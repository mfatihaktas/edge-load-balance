import threading, time, sys, getopt, json, queue, nslookup
from collections import deque

from config import *
from priority_dict import *
from debug_utils import *
from commer import CommerOnMaster, LISTEN_IP, send_msg
from msg import Msg, InfoType, UpdateType, Update
from plot import plot_master

def get_wip_s(domain):
	query = nslookup.Nslookup()
	record = query.dns_lookup(domain)
	log(DEBUG, "", dns_response=record.response_full, dns_answer=record.answer)

	return set(record.answer)

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
	def __init__(self, wip_s, w_token_q, max_qlen):
		self.w_token_q = w_token_q
		self.max_qlen = max_qlen

		self.wip_qlen_heap_m = priority_dict()
		for wip in wip_s:
			self.wip_qlen_heap_m[wip] = 0

			for _ in range(self.max_qlen):
				self.w_token_q.put(1)

		self.lock = threading.Lock()
		log(DEBUG, "WQueue constructed", w_token_q_len=self.w_token_q.qsize(), wip_s=wip_s)

	def update(self, new_wip_s):
		log(DEBUG, "started", new_wip_s=new_wip_s)
		with self.lock:
			## Drop wip's that got removed
			for wip in self.wip_qlen_heap_m:
				if wip not in new_wip_s:
					qlen = self.wip_qlen_heap_m[wip]
					log(DEBUG, "dropping", wip=wip, qlen=qlen)
					for _ in range(self.max_qlen - qlen):
						self.w_token_q.get(block=False)
					self.wip_qlen_heap_m.pop(wip)
			## Add new wip's
			for wip in new_wip_s:
				if wip not in self.wip_qlen_heap_m:
					log(DEBUG, "adding", wip=wip)
					self.wip_qlen_heap_m[wip] = 0
					for _ in range(self.max_qlen):
						self.w_token_q.put(1)
		log(DEBUG, "done")

	def inc_qlen(self, wip):
		log(DEBUG, "started", wip=wip)
		with self.lock:
			self.wip_qlen_heap_m[wip] += 1
			check(self.wip_qlen_heap_m[wip] <= self.max_qlen, "Q-len cannot be greater than max_qlen= {}".format(self.max_qlen))
		log(DEBUG, "done", wip=wip, qlen=self.wip_qlen_heap_m[wip])

	def dec_qlen(self, wip):
		log(DEBUG, "started", wip=wip)
		with self.lock:
			self.wip_qlen_heap_m[wip] -= 1
			check(self.wip_qlen_heap_m[wip] >= 0, "Q-len cannot be negative")

			self.w_token_q.put(1)
		log(DEBUG, "done", wip=wip, qlen=self.wip_qlen_heap_m[wip])

	def pop(self):
		with self.lock:
			wip = self.wip_qlen_heap_m.smallest()
			qlen = self.wip_qlen_heap_m[wip]
		if qlen >= self.max_qlen:
			log(WARNING, "Attempted to return a full worker", qlen=qlen)
			return None
		return wip

class Master():
	def __init__(self, _id, wip_s, dashboard_server_ip, worker_service=None):
		self._id = _id
		self.wip_s = wip_s
		self.dashboard_server_ip = dashboard_server_ip
		self.worker_service = worker_service

		if self.wip_s is None:
			check(self.worker_service is not None, "If wip is None, worker_service should NOT be None")
			self.wip_s = self.get_wip_s()

		self.commer = CommerOnMaster(self._id, self.handle_msg)

		self.msg_token_q = queue.Queue()
		self.msg_q = RRQueue(max_qlen=5)

		self.w_token_q = queue.Queue()
		self.w_q = WQueue(self.wip_s, self.w_token_q, max_qlen=30)

		if worker_service is not None:
			t_wip_update = threading.Thread(target=self.run_wip_updates, daemon=True)
			t_wip_update.start()

		if self.dashboard_server_ip is not None:
			self.num_updates_sent = 0
			t_dashboard_update = threading.Thread(target=self.run_dashboard_updates, daemon=True)
			t_dashboard_update.start()

		self.on = True
		t = threading.Thread(target=self.run, daemon=True)
		t.start()
		t.join()

	def __repr__(self):
		return "Master(id= {}, wip_s= {})".format(self._id, self.wip_s)

	def close(self):
		log(DEBUG, "started")
		self.commer.close()
		self.on = False
		log(DEBUG, "done")

	def get_wip_s(self):
		wip_s = get_wip_s(self.worker_service)
		while len(wip_s) == 0:
			time.sleep(0.1)

			log(DEBUG, "get_wip_s returned empty...retrying", worker_service=self.worker_service)
			wip_s = get_wip_s(self.worker_service)
		return wip_s

	def run_wip_updates(self):
		while self.on:
			time.sleep(5)

			new_wip_s = self.get_wip_s()
			self.w_q.update(new_wip_s)

	def send_update_to_dashboard(self):
		# log(DEBUG, "started")
		self.num_updates_sent += 1

		m = {'mid': self._id,
				 'epoch': time.time(),
				 'w_qlen_l': [qlen for wip, qlen in self.w_q.wip_qlen_heap_m.items()]}

		msg = Msg(_id = self.num_updates_sent,
							payload = Update(_id=self.num_updates_sent, typ=UpdateType.from_master, m=m),
							src_id = self._id,
							src_ip = LISTEN_IP,
							dst_id = 'd',
							dst_ip = self.dashboard_server_ip)
		send_msg(msg)

		log(DEBUG, "done", m=m)

	def run_dashboard_updates(self):
		while True:
			time.sleep(1)

			self.send_update_to_dashboard()

	def handle_msg(self, msg):
		log(DEBUG, "handling", msg=msg)

		p = msg.payload
		if p.is_req():
			p.epoch_arrived_cluster = time.time()
			if self.msg_q.push(msg):
				self.msg_token_q.put(1)
		elif p.is_info():
			if p.typ == InfoType.client_disconn:
				# self.msg_q.unreg(msg.src_id)
				pass
			elif p.typ == InfoType.worker_req_completion:
				self.w_q.dec_qlen(msg.src_ip)
			elif p.typ == InfoType.close:
				for wip in self.wip_s:
					self.commer.send_to_worker(wip, msg)
				self.close()
		else:
			log(ERROR, "Unexpected payload type", payload=p)

	def run(self):
		while self.on:
			log(DEBUG, "Waiting for msg")
			self.msg_token_q.get(block=True)
			msg = self.msg_q.pop()
			check(msg is not None, "Msg must have arrived")

			log(DEBUG, "Waiting for worker")
			self.w_token_q.get(block=True)
			log(DEBUG, "", w_token_q_len=self.w_token_q.qsize())
			wip = self.w_q.pop()
			check(wip is not None, "There should have been an available worker")

			log(DEBUG, "Will send_to_worker", wip=wip)
			self.commer.send_to_worker(wip, msg)
			if msg.payload.is_req():
				log(DEBUG, "Will inc_qlen", wip=wip)
				self.w_q.inc_qlen(wip)

def parse_argv(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['log_to_std=', 'i=', 'wip_l=', 'worker_service=', 'dashboard_server_ip='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		if opt == '--log_to_std':
			m['log_to_std'] = bool(int(arg))
		elif opt == '--i':
			m['i'] = arg
		elif opt == '--wip_l':
			m['wip_s'] = set(json.loads(arg))
		elif opt == '--worker_service':
			m['worker_service'] = arg
		elif opt == '--dashboard_server_ip':
			m['dashboard_server_ip'] = arg
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	if 'log_to_std' not in m:
		m['log_to_std'] = True
	if 'i' not in m:
		m['i'] = LISTEN_IP
	if 'wip_s' not in m:
		m['wip_s'] = None
	if 'dashboard_server_ip' not in m:
		m['dashboard_server_ip'] = 'dashboard-service'

	log(DEBUG, "", m=m)
	return m

def run(argv):
	m = parse_argv(argv)
	_id = 'm_' + m['i']
	log_to_file('{}.log'.format(_id))
	if m['log_to_std']:
		log_to_std()
	log(DEBUG, "", m=m)

	mr = Master(_id, m['wip_s'],
							dashboard_server_ip=m['dashboard_server_ip'])
	# input("Enter to finish...\n")
	# sys.exit()

if __name__ == '__main__':
	run(sys.argv[1:])
