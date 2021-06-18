import threading, time, sys, getopt, json, queue, enum

from config import *
from rvs import *
from msg import *
from commer import PACKET_SIZE, IP_ETH0, CommerOnClient
from plot import plot_client

class State(enum.Enum):
	on = 1
	off = 2

class Client():
	def __init__(self, _id, d, inter_probe_num_reqs,
							 mid_ip_m, num_reqs_to_finish, inter_gen_time_rv, serv_time_rv, size_inBs_rv):
		self._id = _id
		self.d = d
		self.inter_probe_num_reqs = inter_probe_num_reqs
		self.mid_ip_m = mid_ip_m
		self.num_reqs_to_finish = num_reqs_to_finish
		self.inter_gen_time_rv = inter_gen_time_rv
		self.serv_time_rv = serv_time_rv
		self.size_inBs_rv = size_inBs_rv

		self.mid_l = []
		self.commer = CommerOnClient(_id, self.handle_msg)
		for mid, mip in mid_ip_m.items():
			self.commer.reg(mid, mip)
			self.mid_l.append(mid)

		self.num_reqs_gened = 0
		self.num_reqs_finished = 0
		self.num_reqs_last_probed = 0

		self.req_finished_l = []
		self.last_time_result_recved = time.time()
		self.inter_result_time_l = []

		self.assigned_mid = random.sample(self.mid_l, 1)[0]
		self.waiting_for_probe = False
		#self.wait_for_probe = threading.Condition()
		self.state = State.on

		self.msg_recved_q = queue.Queue()
		t_recv = threading.Thread(target=self.run_recv, daemon=True)
		t_recv.start()

		t = threading.Thread(target=self.run_send, daemon=True)
		t.start()
		t.join()

	def __repr__(self):
		return 'Client(' + '\n\t' + \
			'id= {}'.format(self._id) + '\n\t' + \
			'inter_probe_num_reqs= {}'.format(self.inter_probe_num_reqs) + '\n\t' + \
			'mid_ip_m= {}'.format(self.mid_ip_m) + '\n\t' + \
			'num_reqs_to_finish= {}'.format(self.num_reqs_to_finish) + '\n\t' + \
			'serv_time_rv= {}'.format(self.serv_time_rv) + '\n\t' + \
			'size_inBs_rv= {}'.format(self.size_inBs_rv) + ')'

	def close(self):
		if self.state == State.off:
			return

		log(DEBUG, "started")
		self.state = State.off
		self.commer.close()
		log(DEBUG, "done")

	def handle_msg(self, msg):
		log(DEBUG, "recved", msg=msg)
		self.msg_recved_q.put(msg)

	def run_recv(self):
		while True:
			msg = self.msg_recved_q.get(block=True)

			log(DEBUG, "handling", msg=msg)
			check(msg.payload.is_result(), "Msg should contain a result")
			result = msg.payload
			check(result.cid == self._id, "result.cid should equal to cid")

			if result.probe:
				if self.waiting_for_probe:
					if self.assigned_mid != msg.src_id:
						msg_ = Msg(0, payload=Info(0, InfoType.client_disconn), src_id=self._id, src_ip=IP_ETH0)
						self.commer.send_msg(self.assigned_mid, msg_)

					self.assigned_mid = result.mid
					self.num_reqs_last_probed = self.num_reqs_gened
					self.waiting_for_probe = False
					log(DEBUG, "Set conned mid", assigned_mid=self.assigned_mid)
				else:
					log(DEBUG, "Late probe result has been recved", msg=msg)
					continue

			## Book keeping
			log(DEBUG, "started book keeping", msg=msg)
			t = time.time()
			result.epoch_arrived_client = t
			self.req_finished_l.append(result)

			log(DEBUG, "",
					response_time = (result.epoch_arrived_client - result.epoch_departed_client),
					time_from_c_to_s = (result.epoch_arrived_cluster - result.epoch_departed_client),
					time_from_s_to_c = (result.epoch_arrived_client - result.epoch_departed_cluster),
					time_from_s_to_w_to_s = result.serv_time,
					result=result)

			inter_result_time = t - self.last_time_result_recved
			self.inter_result_time_l.append(inter_result_time)
			self.last_time_result_recved = t
			log(DEBUG, "", inter_result_time=inter_result_time, job_serv_time=result.serv_time)

			self.num_reqs_finished += 1
			log(DEBUG, "", num_reqs_gened=self.num_reqs_gened, num_reqs_finished=self.num_reqs_finished)

			log(DEBUG, "done", msg_id=msg._id)
			if self.num_reqs_finished >= self.num_reqs_to_finish:
				self.close()

	def replicate(self, mid_l, msg):
		log(DEBUG, "started", mid_l=mid_l, msg=msg)
		# TODO: Send to masters in parallel
		for mid in mid_l:
			self.commer.send_msg(mid, msg)
			log(DEBUG, "sent", mid=mid)
		log(DEBUG, "done")

	def run_send(self):
		while self.state == State.on:
			self.num_reqs_gened += 1
			req = Request(_id = self.num_reqs_gened,
										size_inBs = int(self.size_inBs_rv.sample()),
										cid = self._id,
										cip = IP_ETH0,
										serv_time = self.serv_time_rv.sample())
			req.epoch_departed_client = time.time()
			msg = Msg(_id=self.num_reqs_gened, payload=req)

			## Send message to currently assigned master
			self.commer.send_msg(self.assigned_mid, msg)
			log(DEBUG, "sent", req=req, assigned_mid=self.assigned_mid)

			## Send also its probe version if need to
			if self.num_reqs_gened == 1 or \
				 self.num_reqs_gened - self.num_reqs_last_probed >= self.inter_probe_num_reqs:
				msg.payload.probe = True
				self.waiting_for_probe = True
				self.replicate(random.sample(self.mid_l, self.d), msg)

			inter_gen_time = self.inter_gen_time_rv.sample()
			log(DEBUG, "sleeping", inter_gen_time=inter_gen_time)
			time.sleep(inter_gen_time)

		if self._id == 'c0':
			log(DEBUG, "Will send close msg to all masters")
			time.sleep(1)
			msg = Msg(_id=0, payload=Info(0, InfoType.close))
			for mid in self.mid_l:
				self.commer.send_msg(mid, msg)
		log(DEBUG, "done")

def parse_argv(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['i=', 'mid_ip_m='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		if opt == '--i':
			m['i'] = arg
		elif opt == '--mid_ip_m':
			m['mid_ip_m'] = json.loads(arg)
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	return m

def run(argv):
	m = parse_argv(argv)
	_id = 'c' + m['i']
	log_to_file('{}.log'.format(_id))

	ES = 0.1 # 0.01
	mu = float(1/ES)
	c = Client(_id, d = 1, inter_probe_num_reqs = float('Inf'),
						 mid_ip_m = m['mid_ip_m'],
						 num_reqs_to_finish = 100,
						 inter_gen_time_rv = DiscreteRV(p_l=[1], v_l=[0.1*1000], norm_factor=1000),
						 serv_time_rv=DiscreteRV(p_l=[1], v_l=[ES*1000], norm_factor=1000), # Exp(mu), # TPareto_forAGivenMean(l=ES/2, a=1, mean=ES)
						 size_inBs_rv=DiscreteRV(p_l=[1], v_l=[PACKET_SIZE*1]))

	time.sleep(3)
	log(DEBUG, "", client=c)
	plot_client(c)

	c.close()
	sys.exit()

if __name__ == '__main__':
	run(sys.argv[1:])
