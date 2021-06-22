import threading, time, sys, getopt, json, queue, nslookup
from collections import deque

from config import *
from priority_dict import *
from debug_utils import *
from commer import CommerOnMaster, LISTEN_IP, send_msg
from msg import Msg, InfoType, UpdateType, Update
from plot import plot_master

def get_wip_l(domain):
	query = nslookup.Nslookup()
	record = query.dns_lookup(domain)
	log(DEBUG, "", dns_response=record.response_full, dns_answer=record.answer)

	return record.answer

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

		q = self.cid_q_m[msg.payload.cid]
		if len(q) == self.max_qlen:
			msg_popped = q.popleft()
			log(DEBUG, "Was full, popped the oldest req", msg_popped=msg_popped)
			self.num_dropped += 1
		q.append(msg)
		log(DEBUG, "pushed", msg=msg)

	def pop(self):
		for _ in range(len(self.cid_q_m)):
			q = self.cid_q_m[self.next_cid_to_pop_q[0]]
			self.next_cid_to_pop_q.rotate(-1)
			if len(q) > 0:
				return q.popleft()
		return None

class WQueue(): # Worker
	def __init__(self, wip_l, w_token_q, max_qlen):
		self.w_token_q = w_token_q
		self.max_qlen = max_qlen

		self.wip_qlen_heap_m = priority_dict()
		for wip in wip_l:
			self.wip_qlen_heap_m[wip] = 0

			for _ in range(self.max_qlen):
				self.w_token_q.put(1)

		self.lock = threading.Lock()
		log(DEBUG, "WQueue constructed", w_token_q_len=self.w_token_q.qsize(), wip_l=wip_l)

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
	def __init__(self, _id, wip_l, dashboard_server_ip=None):
		self._id = _id
		self.wip_l = wip_l
		self.dashboard_server_ip = dashboard_server_ip

		self.commer = CommerOnMaster(self._id, self.handle_msg)

		self.msg_token_q = queue.Queue()
		self.msg_q = RRQueue(max_qlen=5)

		self.w_token_q = queue.Queue()
		self.w_q = WQueue(self.wip_l, self.w_token_q, max_qlen=30)

		self.num_updates_sent = 0

		self.on = True
		t = threading.Thread(target=self.run, daemon=True)
		t.start()
		t.join()

	def __repr__(self):
		return "Master(id= {}, wip_l= {})".format(self._id, self.wip_l)

	def close(self):
		self.commer.close()
		self.on = False
		log(DEBUG, "done")

	def send_update_to_dashboard(self):
		if self.dashboard_server_ip is None:
			return

		log(DEBUG, "started")
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

	def handle_msg(self, msg):
		log(DEBUG, "handling", msg=msg)

		p = msg.payload
		if p.is_req():
			p.epoch_arrived_cluster = time.time()
			self.msg_q.push(msg)
			self.msg_token_q.put(1)
		elif p.is_info():
			if p.typ == InfoType.client_disconn:
				self.msg_q.unreg(msg.src_id)
			elif p.typ == InfoType.worker_req_completion:
				self.w_q.dec_qlen(msg.src_ip)
				self.send_update_to_dashboard()
			elif p.typ == InfoType.close:
				for wip in self.wip_l:
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
			log(DEBUG, "Will inc_qlen", wip=wip)
			self.w_q.inc_qlen(wip)

			self.send_update_to_dashboard()

def parse_argv(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['i=', 'wip_l=', 'dashboard_server_ip='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		if opt == '--i':
			m['i'] = arg
		elif opt == '--wip_l':
			m['wip_l'] = json.loads(arg)
		elif opt == '--dashboard_server_ip':
			m['dashboard_server_ip'] = arg
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	if 'i' not in m:
		m['i'] = LISTEN_IP

	if 'wip_l' not in m:
		m['wip_l'] = get_wip_l('edge-service')

	if 'dashboard_server_ip' not in m:
		m['dashboard_server_ip'] = 'dashboard-service'

	log(DEBUG, "", m=m)
	return m

def run(argv):
	m = parse_argv(argv)
	_id = 'm_' + m['i']
	log_to_file('{}.log'.format(_id))
	log(DEBUG, "", m=m)

	mr = Master(_id, m['wip_l'],
							dashboard_server_ip=m['dashboard_server_ip'])
	# input("Enter to finish...\n")
	# sys.exit()

if __name__ == '__main__':
	run(sys.argv[1:])
