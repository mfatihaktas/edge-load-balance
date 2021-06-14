import threading, time, sys, getopt, queue

from debug_utils import *
from commer import CommerOnWorker
from msg import result_from_req, Info

class Worker():
	def __init__(self, _id):
		self._id = _id

		self.msg_q = queue.Queue()
		self.commer = CommerOnWorker(_id, self.msg_q)

		t = threading.Thread(target=self.run, daemon=True)
		t.start()
		t.join()

	def close(self):
		log(DEBUG, "started")
		self.commer.close()
		log(DEBUG, "done")

	def run(self):
		while True:
			msg = self.msg_q.get(block=True)
			if msg is None:
				log(DEBUG, "recved close signal")
				self.close()
				return

			# TODO: real processing goes in here
			req = msg.payload
			log(DEBUG, "serving/sleeping", serv_time=req.serv_time)
			time.sleep(req.serv_time)
			log(DEBUG, "finished serving")

			## Empty info is interpreted as a request completion at the master
			msg.payload = Info(req._id, {})
			self.commer.send_info(msg)

			result = result_from_req(req)
			# result.size_inBs = ?
			msg.payload = result
			self.commer.send_result(msg)

def parse_argv(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['i='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		if opt == '--i':
			m['i'] = arg
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	return m

if __name__ == '__main__':
	m = parse_argv(sys.argv[1:])
	_id = 'w' + m['i']
	log_to_file('{}.log'.format(_id))

	w = Worker(_id)

	input("Enter to finish...\n")
	sys.exit()
