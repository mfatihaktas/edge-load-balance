import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import threading, queue
from collections import deque

from debug_utils import *
from plot_utils import *
from commer import TCPServer, LISTEN_IP, LISTEN_PORT
from msg import Update, UpdateType

class CommerOnDashboardServer():
	def __init__(self, handle_msg):
		self.server_to_recv_updates = TCPServer((LISTEN_IP, LISTEN_PORT), handle_msg)
		self.server_to_recv_updates_thread = threading.Thread(target=self.server_to_recv_updates.serve_forever, daemon=True)
		self.server_to_recv_updates_thread.start()

	def close(self):
		log(DEBUG, "started")
		self.server_to_recv_updates.shutdown()
		log(DEBUG, "done")

class InfoQ():
	def __init__(self, max_qlen):
		self.max_qlen = max_qlen

		self.id__info_m_q = {}

	def __repr__(self):
		return pprint.pformat(self.id__info_m_q)

	def put(self, _id, info_m):
		log(DEBUG, "started", id=_id, info_m=info_m)

		if _id not in self.id__info_m_q:
			self.id__info_m_q[_id] = deque(maxlen=self.max_qlen)
		q = self.id__info_m_q[_id]
		q.append(info_m)

		log(DEBUG, "done", id=_id)

	def get_info_m_q(self, _id):
		return self.id__info_m_q[_id]

class ClientInfo():
	def __init__(self):
		self.client_info_q = InfoQ(max_qlen=20)

	def __repr__(self):
		return 'ClientInfo:\n' + \
			     '\t client_info_q=\n {}'.format(self.client_info_q)

	def put(self, req_info_m):
		cid = req_info_m['cid']
		log(DEBUG, "started", cid=cid)
		self.client_info_q.put(cid, req_info_m)
		self.plot(cid)
		log(DEBUG, "done")

	def plot(self, cid):
		log(DEBUG, "started", cid=cid)
		info_m_q = self.client_info_q.get_info_m_q(cid)

		fontsize = 14
		## T over requests
		i = 0
		while i < len(info_m_q):
			_i = i
			T_l = []
			while i < len(info_m_q) and (i == 0 or info_m_q[i]['mid'] == info_m_q[i-1]['mid']):
				T_l.append(info_m_q[i]['T'])
				i += 1
			x_l = list(range(_i, i))
			plot.plot(x_l, T_l, label='mid= {}'.format(info_m_q[i-1]['mid']), color=next(nice_color), marker='x', linestyle='None', mew=3, ms=5)
			plot.xticks([])

		plot.legend(fontsize=fontsize)
		plot.ylabel('T (msec)', fontsize=fontsize)
		# plot.xlabel('t', fontsize=fontsize)
		plot.title('cid= {}'.format(cid))
		plot.gcf().set_size_inches(6, 4)
		plot.savefig("static/image/plot_{}.png".format(cid), bbox_inches='tight')
		plot.gcf().clear()
		log(DEBUG, "done", cid=cid)

class MasterInfo():
	def __init__(self):
		self.master_info_q = InfoQ(max_qlen=20)

	def __repr__(self):
		return 'MasterInfo:\n' + \
			     '\t master_info_q=\n {}'.format(self.master_info_q)

	def put(self, info_m):
		mid = info_m['mid']
		log(DEBUG, "started", mid=mid)
		self.master_info_q.put(mid, info_m)
		self.plot(mid)
		log(DEBUG, "done")

	def plot(self, mid):
		log(DEBUG, "started", mid=mid)
		info_m_q = self.master_info_q.get_info_m_q(mid)

		fontsize = 14
		## Worker load over time
		te = info_m_q[-1]['epoch']
		x_l, y_l, yerr_l = [], [], []
		for info_m in info_m_q:
			x_l.append(te - info_m['epoch'])

			w_qlen_l = info_m['w_qlen_l']
			w_qlen_mean, w_qlen_std = np.mean(w_qlen_l), np.std(w_qlen_l)
			y_l.append(w_qlen_mean)
			yerr_l.append(w_qlen_std)

		plot.errorbar(x_l, y_l, yerr=yerr_l, color=next(nice_color), marker='o', linestyle='None', mew=3, ms=5)
		# plot.legend(fontsize=fontsize)
		plot.xlabel('Time (sec)', fontsize=fontsize)
		plot.ylabel('Avg worker queue length', fontsize=fontsize)
		plot.title('mid= {}'.format(mid))
		plot.gcf().set_size_inches(6, 4)
		plot.savefig("static/image/plot_{}.png".format(mid), bbox_inches='tight')
		plot.gcf().clear()
		log(DEBUG, "done", mid=mid)

class DashboardServer():
	def __init__(self):
		self.commer = CommerOnDashboardServer(self.handle_msg)

		self.client_info = ClientInfo()
		self.master_info = MasterInfo()

		self.msg_q = queue.Queue()

		t = threading.Thread(target=self.run, daemon=True)
		t.start()
		# t.join()

	def close(self):
		self.commer.close()
		self.on = False
		log(DEBUG, "done")

	def handle_msg(self, msg):
		self.msg_q.put(msg)

	def run(self):
		while True:
			msg = self.msg_q.get(block=True)

			update = msg.payload
			if update.typ == UpdateType.from_client:
				self.client_info.put(update.m)
			elif update.typ == UpdateType.from_master:
				self.master_info.put(update.m)
			else:
				assert_("Unexpected update type", update=update)
