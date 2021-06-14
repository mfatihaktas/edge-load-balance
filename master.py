import threading, time, sys, getopt, json, queue, nslookup

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

class Master():
	def __init__(self, _id, wip_l=None, worker_service_domain='edge-server'):
		self._id = _id
		self.wip_l = wip_l if wip_l is not None else get_wip_l(worker_service_domain)

		self.commer = CommerOnMaster(_id, self.handle_msg)

		self.msg_req_q = queue.Queue()
		self.wip_qlen_heap_m = priority_dict()
		for wip in self.wip_l:
			self.wip_qlen_heap_m[wip] = 0

		self.lock = threading.Lock()
		t = threading.Thread(target=self.run, daemon=True)
		t.start()
		t.join()

	def __repr__(self):
		return "Master(id= {}, wip_l= {})".format(self._id, self.wip_l)

	def handle_msg(self, msg):
		log(DEBUG, "handling", msg=msg)

		p = msg.payload
		if p.is_req():
			self.msg_req_q.put(p)
		elif p.is_info():
			## Any info from a worker indicates a request completion
			with self.lock:
				self.wip_qlen_heap_m[msg.src_ip] -= 1
				check(self.wip_qlen_heap_m[msg.src_ip] >= 0, "Q-len cannot be negative")
		else:
			log(ERROR, "Unexpected payload type", payload=payload)

	def run(self):
		while True:
			msg_req = self.msg_req_q.get(block=True)

			with self.lock:
				wip = self.wip_qlen_heap_m.smallest()

			self.commer.send_to_worker(wip, msg_req)

			with self.lock:
				self.wip_qlen_heap_m[wip] += 1

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

	s = Server(_id, m['wip_l'])
	# input("Enter to finish...\n")
	# sys.exit()

def test(argv):
	m = parse_argv(argv)
	_id = 's' + m['i']
	log_to_file('{}.log'.format(_id))

	s = Server(_id, m['wip_l'])
	input("Enter to finish...\n")
	sys.exit()

if __name__ == '__main__':
	if TEST:
		test(sys.argv[1:])
	else:
		run(sys.argv[1:])
