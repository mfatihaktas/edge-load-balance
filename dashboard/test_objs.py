import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import threading, time, random, getopt

from debug_utils import *
from commer import LISTEN_IP, send_msg
from msg import Msg, UpdateType, Update

class TestClient():
	def __init__(self, _id, inter_update_time, dashboard_server_ip):
		self._id = _id
		self.inter_update_time = inter_update_time
		self.dashboard_server_ip = dashboard_server_ip

		t = threading.Thread(target=self.run, daemon=True)
		t.start()

	def send_update(self, m):
		msg = Msg(_id = 0,
							payload = Update(_id=0, typ=UpdateType.from_client, m=m),
							src_id = self._id,
							src_ip = LISTEN_IP,
							dst_id = 'd',
							dst_ip = self.dashboard_server_ip)
		send_msg(msg)
		log(DEBUG, "done")

	def run(self):
		while True:
			time.sleep(self.inter_update_time)

			mid = random.randint(1, 3)
			m = {'cid': self._id,
					 'mid': 'cl-{}'.format(mid),
					 'T': random.randint(1, 10)}
			self.send_update(m)

class TestMaster():
	def __init__(self, _id, num_worker, inter_update_time, dashboard_server_ip):
		self._id = _id
		self.num_worker = num_worker
		self.inter_update_time = inter_update_time
		self.dashboard_server_ip = dashboard_server_ip

		t = threading.Thread(target=self.run, daemon=True)
		t.start()

	def send_update(self, m):
		msg = Msg(_id = 0,
							payload = Update(_id=0, typ=UpdateType.from_master, m=m),
							src_id = self._id,
							src_ip = LISTEN_IP,
							dst_id = 'd',
							dst_ip = self.dashboard_server_ip)
		send_msg(msg)
		log(DEBUG, "done")

	def run(self):
		epoch = 0
		while True:
			time.sleep(self.inter_update_time)

			m = {'mid': self._id,
					 'epoch': epoch,
					 'w_qlen_l': [random.randint(1, 10) for _ in range(self.num_worker)]}
			epoch += random.randint(1, 5)
			self.send_update(m)

def parse_argv(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['dashboard_server_ip='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		if opt == '--dashboard_server_ip':
			m['dashboard_server_ip'] = arg
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	log(DEBUG, "", m=m)
	return m

if __name__ == '__main__':
	log_to_std()

	m = parse_argv(sys.argv[1:])
	tc = TestClient(_id='c_0', inter_update_time=0.1, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestClient(_id='c_1', inter_update_time=0.1, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestClient(_id='c_2', inter_update_time=0.1, dashboard_server_ip=m['dashboard_server_ip'])

	tc = TestMaster(_id='m_0', num_worker=10, inter_update_time=0.2, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestMaster(_id='m_1', num_worker=10, inter_update_time=0.25, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestMaster(_id='m_2', num_worker=10, inter_update_time=0.2, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestMaster(_id='m_3', num_worker=10, inter_update_time=0.25, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestMaster(_id='m_4', num_worker=10, inter_update_time=0.2, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestMaster(_id='m_5', num_worker=10, inter_update_time=0.25, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestMaster(_id='m_6', num_worker=10, inter_update_time=0.2, dashboard_server_ip=m['dashboard_server_ip'])
	tc = TestMaster(_id='m_7', num_worker=10, inter_update_time=0.25, dashboard_server_ip=m['dashboard_server_ip'])

	input("Enter...")
