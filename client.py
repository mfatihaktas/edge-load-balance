import threading, time, sys, getopt, json, queue, enum

from config import *
from plot_utils import *
from rvs import *
from msg import *
from commer import PACKET_SIZE, IP_ETH0, CommerOnClient

class State(enum.Enum):
	probe = 1
	push = 2
	off = 3

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

		self.req_finished_l = []
		self.last_time_result_recved = time.time()
		self.inter_result_time_l = []

		self.conned_mid = None
		self.wait_for_probe = threading.Condition()
		self.state = State.probe
		t = threading.Thread(target=self.run, daemon=True)
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
		log(DEBUG, "started", msg=msg)

		check(msg.payload.is_result(), "Msg should contain a result")
		result = msg.payload

		t = time.time()
		result.epoch_arrived_client = t

		self.req_finished_l.append(result)

		log(DEBUG, "",
				response_time = (result.epoch_arrived_client - result.epoch_departed_client),
				time_from_c_to_s = (result.epoch_arrived_server - result.epoch_departed_client),
				time_from_s_to_c = (result.epoch_arrived_client - result.epoch_departed_server),
				time_from_s_to_w_to_s = result.serv_time,
				num_server_fair_share = result.num_server_fair_share,
				result=result)

		inter_result_time = t - self.last_time_result_recved
		self.inter_result_time_l.append(inter_result_time)
		self.last_time_result_recved = t
		log(DEBUG, "", inter_result_time=inter_result_time, job_serv_time=result.serv_time)

		self.num_reqs_finished += 1
		log(DEBUG, "", num_reqs_gened=self.num_reqs_gened, num_reqs_finished=self.num_reqs_finished)

		if result.probe and self.state == State.probe:
			notify_wait_for_probe = self.conned_mid is None
			self.conned_mid = msg.src_id
			self.state = State.push

			if notify_wait_for_probe:
				with self.wait_for_probe:
					self.wait_for_probe.notifyAll()
					log(DEBUG, "wait_for_probe notified")

		log(DEBUG, "done", msg_id=msg._id)
		if self.num_reqs_finished >= self.num_reqs_to_finish:
			self.close()

	def replicate(self, mid_l, msg):
		log(DEBUG, "started", mid_l=mid_l, msg=msg)
		for mid in mid_l:
			self.commer.send_msg(mid, msg)
			log(DEBUG, "sent", mid=mid)
		log(DEBUG, "done")

	def run(self):
		while True:
			if self.state == State.off:
				log(DEBUG, "Closed, terminating")
				break

			self.num_reqs_gened += 1
			req = Request(_id = self.num_reqs_gened,
										size_inBs = int(self.size_inBs_rv.sample()),
										cid = self._id,
										cip = IP_ETH0,
										serv_time = self.serv_time_rv.sample())
			req.epoch_departed_client = time.time()
			msg = Msg(_id=self.num_reqs_gened, payload=req)

			if self.state == State.probe:
				msg.payload.probe = True

				if self.conned_mid is None:
					self.replicate(self.mid_l, msg)

					with self.wait_for_probe:
						log(DEBUG, "waiting for first probe")
						self.wait_for_probe.wait()
				else:
					self.replicate(random.sample(self.mid_l, self.d), msg)

				self.num_reqs_last_probed = self.num_reqs_gened
				self.state = State.push
			else: # self.state = State.push
				self.commer.send_msg(self.conned_mid, msg)
				log(DEBUG, "sent", req=req, conned_mid=self.conned_mid)

				if self.num_reqs_gened - self.num_reqs_last_probed >= self.inter_probe_num_reqs:
					self.state = State.probe

				inter_gen_time = self.inter_gen_time_rv.sample()
				log(DEBUG, "sleeping", inter_gen_time=inter_gen_time)
				time.sleep(inter_gen_time)

		log(DEBUG, "done")

def plot_response_time(self, c):
	fontsize = 14
	## T over time
	t0 = self.req_finished_l[0].epoch_arrived_client
	t_l, T_l = [], []
	for req in self.req_finished_l:
		t_l.append(req.epoch_arrived_client - t0)
		T_l.append(1000*(req.epoch_arrived_client - req.epoch_departed_client))
	plot.ylabel('T (msec)', fontsize=fontsize)
	plot.xlabel('t', fontsize=fontsize)
	plot.legend(fontsize=fontsize)
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_{}_T_over_t.png".format(self._id), bbox_inches='tight')
	plot.gcf().clear()

	## CDF of T
	add_cdf(T_l, plot.gca(), sid, next(nice_color)) # drawline_x_l=[1000*self.max_delay]
	plot.xscale('log')
	plot.xticks(rotation=70)
	plot.ylabel('Pr{T < x}', fontsize=fontsize)
	plot.xlabel('x (msec)', fontsize=fontsize)
	plot.legend(fontsize=fontsize)
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_{}_cdf_T.png".format(self._id), bbox_inches='tight')
	plot.gcf().clear()

	## CDF of inter result times
	add_cdf(self.inter_result_time_l, plot.gca(), '', next(nice_color)) # drawline_x_l=[1000*self.inter_job_gen_time_rv.mean()]
	plot.xscale('log')
	plot.xticks(rotation=70)
	plot.ylabel('Pr{Inter result time < x}', fontsize=fontsize)
	plot.xlabel('x (msec)', fontsize=fontsize)
	plot.legend(fontsize=fontsize)
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_{}_cdf_interResultTime.png".format(self._id), bbox_inches='tight')

	log(DEBUG, "done.")

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
						 inter_gen_time_rv = DiscreteRV(p_l=[1], v_l=[1]),
						 serv_time_rv=DiscreteRV(p_l=[1], v_l=[ES*1000], norm_factor=1000), # Exp(mu), # TPareto_forAGivenMean(l=ES/2, a=1, mean=ES)
						 size_inBs_rv=DiscreteRV(p_l=[1], v_l=[1]))

	time.sleep(3)
	log(DEBUG, "", client=c)
	plot_response_time(c)

	time.sleep(100000)
	c.close()
	sys.exit()

def test(argv):
	m = parse_argv(argv)
	_id = 'c' + m['i']
	log_to_file('{}.log'.format(_id))

	# input("Enter to start...\n")
	ES = 0.1 # 0.01
	mu = float(1/ES)
	c = Client(_id, d = 1, inter_probe_num_reqs = float('Inf'),
						 mid_ip_m = m['mid_ip_m'],
						 num_reqs_to_finish = 100,
						 inter_gen_time_rv = DiscreteRV(p_l=[1], v_l=[1]),
						 serv_time_rv=DiscreteRV(p_l=[1], v_l=[ES*1000], norm_factor=1000), # Exp(mu), # TPareto_forAGivenMean(l=ES/2, a=1, mean=ES)
						 size_inBs_rv=DiscreteRV(p_l=[1], v_l=[PACKET_SIZE*1]))

	# input("Enter to summarize job info...\n")
	# time.sleep(3)
	log(DEBUG, "", client=c)
	plot_response_time(c)

	# input("Enter to finish...\n")
	# c.close()
	# sys.exit()

if __name__ == '__main__':
	if TEST:
		test(sys.argv[1:])
	else:
		run(sys.argv[1:])
