import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import threading, time, random

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

if __name__ == '__main__':
	tc = TestClient(_id='c0', inter_update_time=1, dashboard_server_ip='192.168.2.148')
	tc = TestClient(_id='c1', inter_update_time=1, dashboard_server_ip='192.168.2.148')
	tc = TestClient(_id='c2', inter_update_time=1, dashboard_server_ip='192.168.2.148')

	tc = TestMaster(_id='cl-0', num_worker=10, inter_update_time=2, dashboard_server_ip='192.168.2.148')
	tc = TestMaster(_id='cl-1', num_worker=10, inter_update_time=2.5, dashboard_server_ip='192.168.2.148')

	input("Enter...")
