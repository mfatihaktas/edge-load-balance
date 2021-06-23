import threading, time, sys, getopt, queue

from debug_utils import *
from commer import CommerOnWorker, LISTEN_IP
from msg import result_from_req, InfoType, Info
from plot import plot_worker

class Worker():
	def __init__(self, _id):
		self._id = _id

		# TODO: Limit queue length
		self.msg_q = queue.Queue()
		self.epoch__num_req_l = []
		self.commer = CommerOnWorker(self._id, self.handle_msg)

		self.on = True
		t = threading.Thread(target=self.run, daemon=True)
		t.start()
		t.join()

	def close(self):
		log(DEBUG, "started")
		self.commer.close()
		self.msg_q.put(None)
		self.on = False
		log(DEBUG, "done")

	def handle_msg(self, msg):
		if msg.payload.is_info() and msg.payload.typ == InfoType.close:
			self.close()
		elif msg.payload.is_req():
			self.msg_q.put(msg)
			self.epoch__num_req_l.append((time.time(), self.msg_q.qsize()))

	def run(self):
		while self.on:
			msg = self.msg_q.get(block=True)
			if msg is None:
				log(DEBUG, "recved close signal")
				self.close()
				return

			# TODO: real processing goes in here
			req = msg.payload
			if not req.probe:
				log(DEBUG, "serving/sleeping", serv_time=req.serv_time)
				time.sleep(req.serv_time)
				log(DEBUG, "finished serving")
				self.epoch__num_req_l.append((time.time(), self.msg_q.qsize()))

				msg.payload = Info(req._id, InfoType.worker_req_completion)
				self.commer.send_info_to_master(msg)

			result = result_from_req(req)
			result.epoch_departed_cluster = time.time()
			# result.size_inBs = ?
			msg.payload = result
			self.commer.send_result_to_user(msg)

		plot_worker(self)

def parse_argv(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['i=', 'log_to_std='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		if opt == '--log_to_std':
			m['log_to_std'] = bool(int(arg))
		elif opt == '--i':
			m['i'] = arg
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	if 'log_to_std' not in m:
		m['log_to_std'] = True
	if 'i' not in m:
		m['i'] = LISTEN_IP

	return m

if __name__ == '__main__':
	m = parse_argv(sys.argv[1:])
	_id = 'w_' + m['i']
	log_to_file('{}.log'.format(_id))
	if m['log_to_std']:
		log_to_std()

	w = Worker(_id)

	# input("Enter to finish...\n")
	# sys.exit()
