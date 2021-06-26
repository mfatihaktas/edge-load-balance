import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import threading, queue, time
from collections import deque

import matplotlib.patches as mpatches

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

	def rm(self, _id):
		log(DEBUG, "started", _id=_id)
		self.id__info_m_q.pop(_id)
		log(DEBUG, "done", _id=_id)

	def get_info_m_q(self, _id):
		return self.id__info_m_q[_id]

class ClientInfo():
	def __init__(self, max_qlen=20):
		self.max_qlen = max_qlen

		self.client_info_q = InfoQ(max_qlen)

		self.mid_color_m = {}

		self.cid_exp_dur = 5
		self.cid__last_time_recved_m = {}
		t = threading.Thread(target=self.run_check_if_any_client_expired, daemon=True)
		t.start()

	def __repr__(self):
		return 'ClientInfo:\n' + \
			     '\t client_info_q=\n {}'.format(self.client_info_q)

	def run_check_if_any_client_expired(self):
		while True:
			time.sleep(7)

			# [(cid, last_time) for cid, last_time self.cid__last_time_recved_m.items()]
			for cid, last_time in list(self.cid__last_time_recved_m.items()):
				if time.time() - last_time > self.cid_exp_dur:
					log(DEBUG, "expired", cid=cid)
					self.cid__last_time_recved_m.pop(cid)
					self.client_info_q.rm(cid)

					fn = self.plot_filename(cid)
					log(DEBUG, "removing", filename=fn)
					try:
						os.remove(fn)
						log(DEBUG, "removed", cid=cid)
					except FileNotFoundError:
						log(WARNING, "file could not be found", filename=fn)

	def put(self, req_info_m):
		cid = req_info_m['cid']
		log(DEBUG, "started", cid=cid)
		self.client_info_q.put(cid, req_info_m)
		self.cid__last_time_recved_m[cid] = time.time()
		log(DEBUG, "done")

	def color_for_mid(self, mid):
		if mid not in self.mid_color_m:
			self.mid_color_m[mid] = next(nice_color)
		return self.mid_color_m[mid]

	def plot_filename(self, cid):
		return "dashboard/static/image/plot_{}.png".format(cid)

	def plot(self, cid):
		log(DEBUG, "started", cid=cid)
		info_m_q = self.client_info_q.get_info_m_q(cid)

		fontsize = 14
		## T over requests
		i = 0
		while i < len(info_m_q):
			_i = i
			T_l = [info_m_q[i]['T']]
			while i < len(info_m_q)-1 and info_m_q[i]['mid'] == info_m_q[i+1]['mid']:
				i += 1
				T_l.append(info_m_q[i]['T'])

			x_l = list(range(_i, i+1))
			# plot.plot(x_l, T_l, label='Cluster id= {}'.format(info_m_q[i-1]['mid']), color=next(nice_color), marker='x', linestyle='None', mew=3, ms=5)
			mid = info_m_q[_i]['mid']
			plot.bar(x_l, height=T_l, color=self.color_for_mid(mid)) # label='Cluster id= {}'.format(mid)
			plot.xticks([])

			if i == _i:
				i += 1

		label_patch_l = []
		for mid, color in self.mid_color_m.items():
			label_patch_l.append(mpatches.Patch(color=color, label='Cluster id= {}'.format(mid)))
		plot.legend(handles=label_patch_l, fontsize=fontsize, bbox_to_anchor=(1.025, 1))
		plot.ylabel('T (msec)', fontsize=fontsize)
		plot.xlabel('The last {} requests (at most)'.format(self.max_qlen), fontsize=fontsize)
		plot.title('Client id= {}'.format(cid))
		plot.gcf().set_size_inches(6, 4)
		plot.savefig(self.plot_filename(cid), bbox_inches='tight')
		plot.gcf().clear()
		log(DEBUG, "done", cid=cid)

class MasterInfo():
	def __init__(self, max_qlen):
		self.max_qlen = max_qlen

		self.master_info_q = InfoQ(max_qlen)

		self.mid_color_m = {}

	def __repr__(self):
		return 'MasterInfo(max_qlen= {})'.format(self.max_qlen) + '\n' \
			     ' : master_info_q=\n {}'.format(self.master_info_q)

	def put(self, info_m):
		mid = info_m['mid']
		log(DEBUG, "started", mid=mid)
		self.master_info_q.put(mid, info_m)
		# self.plot(mid)
		log(DEBUG, "done")

	def color_for_mid(self, mid):
		if mid not in self.mid_color_m:
			self.mid_color_m[mid] = next(nice_color)
		return self.mid_color_m[mid]

	def plot(self, mid):
		log(DEBUG, "started", mid=mid)
		info_m_q = self.master_info_q.get_info_m_q(mid)

		fontsize = 14
		## Worker load over time
		te = info_m_q[-1]['epoch']
		x_l, y_l, yerr_l = [], [], []
		for info_m in info_m_q:
			x_l.append(info_m['epoch'] - te)

			w_qlen_l = info_m['w_qlen_l']
			w_qlen_mean, w_qlen_std = np.mean(w_qlen_l), np.std(w_qlen_l)
			y_l.append(w_qlen_mean)
			yerr_l.append(w_qlen_std)

		plot.errorbar(x_l, y_l, yerr=yerr_l, color=self.color_for_mid(mid), marker='o', linestyle='None', mew=3, ms=5)
		# plot.legend(fontsize=fontsize)
		plot.xlabel('Time (sec)', fontsize=fontsize)
		plot.ylabel('Avg worker queue length', fontsize=fontsize)
		plot.title('Cluster id= {}'.format(mid) + '\n' + '(Error bars show stdev)')
		plot.gcf().set_size_inches(6, 4)
		plot.savefig("dashboard/static/image/plot_{}.png".format(mid), bbox_inches='tight')
		plot.gcf().clear()
		log(DEBUG, "done", mid=mid)

class DashboardServer():
	def __init__(self):
		self.commer = CommerOnDashboardServer(self.handle_msg)

		self.client_info = ClientInfo(max_qlen=50)
		self.master_info = MasterInfo(max_qlen=50)

		self.msg_q = queue.Queue()

		t = threading.Thread(target=self.run, daemon=True)
		t.start()

	def close(self):
		self.commer.close()
		self.on = False
		log(DEBUG, "done")

	def handle_msg(self, msg):
		self.msg_q.put(msg)

	def put(self, update_l):
		cid_plot_s, mid_plot_s = set(), set()
		for update in update_l:
			if update.typ == UpdateType.from_client:
				cid = update.m['cid']
				cid_plot_s.add(cid)
				self.client_info.put(update.m)
			elif update.typ == UpdateType.from_master:
				mid = update.m['mid']
				if mid not in mid_plot_s:
					mid_plot_s.add(mid)
					self.master_info.put(update.m)
			else:
				assert_("Unexpected update type", update=update)

		for cid in cid_plot_s:
			self.client_info.plot(cid)
		for mid in mid_plot_s:
			self.master_info.plot(mid)

	def run(self):
		while True:
			update_l = []
			n = self.msg_q.qsize()
			if n == 0:
				msg = self.msg_q.get(block=True)
				update_l.append(msg.payload)
			else:
				for _ in range(n):
					msg = self.msg_q.get(block=True)
					update_l.append(msg.payload)

			self.put(update_l)
