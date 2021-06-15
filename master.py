import threading, time, sys, getopt, json, queue, nslookup
from collections import deque

from config import *
from priority_dict import *
from debug_utils import *
from commer import CommerOnMaster
from msg import Msg

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

	def reg(self, cid):
		if cid not in self.cid_q_m:
			self.cid_q_m[cid] = deque()
			self.next_cid_to_pop_q.append(cid)
			log(DEBUG, "reged", cid=cid)

	def push(self, msg):
		check(msg.payload.cid in self.cid_q_m, "Req is from an unknown client", msg=msg)
		q = self.cid_q_m[msg.payload.cid]
		if len(q) == self.max_qlen:
			q.popleft()
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

	def inc_qlen(self, wip):
		with self.lock:
			self.wip_qlen_heap_m[wip] += 1
			check(self.wip_qlen_heap_m[wip] <= self.max_qlen, "Q-len cannot be greater than max_qlen= {}".format(self.max_qlen))

	def dec_qlen(self, wip):
		with self.lock:
			self.wip_qlen_heap_m[wip] -= 1
			check(self.wip_qlen_heap_m[wip] >= 0, "Q-len cannot be negative")

			self.w_token_q.put(1)

	def pop(self):
		with self.lock:
			wip = self.wip_qlen_heap_m.smallest()
			qlen = self.wip_qlen_heap_m[wip]
		if qlen >= self.max_qlen:
			log(WARNING, "Attempted to return a full worker", qlen=qlen)
			return None
		return wip

class Master():
	def __init__(self, _id, wip_l=None, worker_service_domain='edge-service'):
		self._id = _id
		self.wip_l = wip_l if wip_l is not None else get_wip_l(worker_service_domain)

		self.commer = CommerOnMaster(_id, self.handle_msg)

		self.msg_token_q = queue.Queue()
		self.msg_q = RRQueue(max_qlen=5)

		self.w_token_q = queue.Queue()
		self.w_q = WQueue(wip_l, self.w_token_q, max_qlen=30)

		t = threading.Thread(target=self.run, daemon=True)
		t.start()
		t.join()

	def __repr__(self):
		return "Master(id= {}, wip_l= {})".format(self._id, self.wip_l)

	def handle_msg(self, msg):
		log(DEBUG, "handling", msg=msg)

		p = msg.payload
		if p.is_req():
			p.epoch_arrived_cluster = time.time()
			self.msg_q.push(msg)
			self.msg_token_q.put(1)
		elif p.is_info():
			## Any info from a worker indicates a request completion
			self.w_q.dec_qlen(msg.src_ip)
		else:
			log(ERROR, "Unexpected payload type", payload=payload)

	def run(self):
		while True:
			self.msg_token_q.get(block=True)
			msg = self.msg_q.pop()
			check(msg is not None, "Msg must have arrived")

			self.w_token_q.get(block=True)
			wip = self.w_q.pop()
			check(wip is not None, "There should have been an available worker")

			self.commer.send_to_worker(wip, msg)
			self.w_q.inc_qlen(wip)

def parse_argv(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['i=', 'wip_l='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		if opt == '--i':
			m['i'] = arg
		elif opt == '--wip_l':
			m['wip_l'] = json.loads(arg)
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))
	log(DEBUG, "", m=m)
	return m

def run(argv):
	m = parse_argv(argv)
	_id = 's' + m['i']
	log_to_file('{}.log'.format(_id))

	mr = Master(_id, m['wip_l'])
	# input("Enter to finish...\n")
	# sys.exit()

def test(argv):
	m = parse_argv(argv)
	_id = 's' + m['i']
	log_to_file('{}.log'.format(_id))

	mr = Master(_id, m['wip_l'])
	input("Enter to finish...\n")
	sys.exit()

if __name__ == '__main__':
	if TEST:
		test(sys.argv[1:])
	else:
		run(sys.argv[1:])
