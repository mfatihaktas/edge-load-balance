import sys, socket, socketserver, getopt, threading, subprocess, json, time

from msg import *
from debug_utils import *

MSG_LEN_HEADER_SIZE = 10
PACKET_SIZE=1024*4 # 1024*10

IP_ETH0 = None # Set below
LISTEN_PORT = 5000
PORT_ON_SERVER_TO_LISTEN_FOR_RESULTS = 4000
PORT_ON_WORKER_TO_LISTEN_FOR_JOBS = 5000

# ***************************  Commer utils  *************************** #
def get_eth0_ip():
	# search and bind to eth0 ip address
	intf_list = subprocess.getoutput("ifconfig -a | sed 's/[ \t].*//;/^$/d'").split('\n')
	intf_eth0 = None
	for intf in intf_list:
		if 'eth0' in intf:
			intf_eth0 = intf

	check(intf_eth0 is not None, "Could not find interface with eth0.")
	intf_eth0_ip = subprocess.getoutput("ip address show dev " + intf_eth0).split()
	intf_eth0_ip = intf_eth0_ip[intf_eth0_ip.index('inet') + 1].split('/')[0]
	return intf_eth0_ip

IP_ETH0 = get_eth0_ip()

def msg_len_header(msg_size):
	msg_size_str = str(msg_size)
	return ('0' * (MSG_LEN_HEADER_SIZE - len(msg_size_str)) + msg_size_str).encode('utf-8')

def create_sock(ip, port):
	log(DEBUG, "started;", ip=ip, port=port)
	try:
		if TRANS == 'TCP':
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((ip, port))
		elif TRANS == 'UDP':
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		return sock
	except IOError as e:
		if e.errno == errno.EPIPE: # insuffient buffer at the server side
			assert_("broken pipe err")
			return None

	log(DEBUG, "done.", ip=ip, port=port)

def bind_get_sock(ip, port):
	if TRANS == 'TCP':
		conn_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		conn_sock.bind((ip, port))
		# conn_sock.listen(1)
		log(DEBUG, "Binded on, listening...", ip=ip, port=port)
		conn_sock.listen()
		sock, addr = conn_sock.accept()
		log(DEBUG, "Got connection", addr=addr)
	elif TRANS == 'UDP':
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind((ip, port))
		log(DEBUG, "Binded on", ip=ip, port=port)

	return sock

def recv_size(size, recv):
	data = bytearray()
	size_to_recv = size
	while size_to_recv > 0:
		data_recved = recv(size_to_recv)
		size_to_recv -= len(data_recved)
		data.extend(data_recved)
	return data

def recv_msg(sock):
	total_size_recved = 0
	recv = lambda size: sock.recv(size)
	msg_len_header = recv_size(MSG_LEN_HEADER_SIZE, recv)
	total_size_recved += MSG_LEN_HEADER_SIZE
	log(DEBUG, "recved header", msg_len_header=msg_len_header)
	msg_len = int(msg_len_header)
	log(DEBUG, "will recv msg", msg_len=msg_len)
	if msg_len == 0:
		return None

	msg_str = recv_size(msg_len, recv)
	msg = msg_from_str(msg_str)
	total_size_recved += len(msg_str)
	log(DEBUG, "recved", msg=msg)

	if msg.payload.size_inBs > 0:
		total_size_to_recv = msg.payload.size_inBs
		log(DEBUG, 'will recv payload', total_size_to_recv=total_size_to_recv)
		while total_size_to_recv > 0:
			size_to_recv = min(total_size_to_recv, PACKET_SIZE)
			data = sock.recv(size_to_recv)
			size_recved = len(data)
			log(DEBUG, 'recved', size=size_recved)
			total_size_to_recv -= size_recved
			total_size_recved += size_recved

		log(DEBUG, "finished recving the payload", size=msg.payload.size_inBs)

	log(DEBUG, "done.", total_size_recved=total_size_recved)
	return msg

def send_msg(msg, trans=TRANS):
	# check(trans != 'UDP' or to_addr is not None, "Trans is UDP but to_addr is None.")
	check(msg.dst_ip is not None, "Dst IP cannot be None")

	sock = create_sock(msg.dst_ip, LISTEN_PORT)
	if msg is None:
		header_ba = bytearray(msg_len_header(0))
		if trans == 'TCP':
			sock.sendall(header_ba)
		elif trans == 'UDP':
			sock.sendto(header_ba, to_addr)
		return

	msg.src_ip = IP_ETH0
	msg_str = msg.to_str().encode('utf-8')
	msg_size = len(msg_str)
	header = msg_len_header(msg_size)

	header_ba = bytearray(header)
	msg_ba = bytearray(msg_str)
	if msg.payload.size_inBs > 0:
		payload_ba = bytearray(msg.payload.size_inBs)

	if trans == 'TCP':
		data = header_ba + msg_ba + payload_ba if msg.payload.size_inBs > 0 else header_ba + msg_ba
		# sock.sendall(data)

		total_size = len(data)
		for i in range(0, total_size, PACKET_SIZE):
			sock.send(data[i:min(i + PACKET_SIZE, total_size)])
		log(DEBUG, "sent", total_size=total_size)

	elif trans == 'UDP':
		sock.sendto(header_ba, to_addr)
		sock.sendto(msg_ba, to_addr)

		if msg.payload.size_inBs > 0:
			total_size = len(payload_ba)
			for i in range(0, total_size, PACKET_SIZE):
				sock.sendto(payload_ba[i:min(i + PACKET_SIZE, total_size)], to_addr)

# ******************************  TCPServer  ***************************** #
class MsgHandler(socketserver.BaseRequestHandler):
	def handle(self):
		msg = recv_msg(sock=self.request)
		log(DEBUG, "recved", msg=msg)

		# self.client_address[0]
		self.server.handle_msg(msg)

class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	def __init__(self, _id, server_addr, handle_msg):
		socketserver.TCPServer.__init__(self, server_addr, MsgHandler)
		self._id = _id
		self.handle_msg = handle_msg

		log(DEBUG, "constructed", server_addr=server_addr)

# ***************************  CommerOnMaster  *************************** #
class CommerOnMaster():
	def __init__(self, _id, handle_msg):
		self._id = _id

		self.server_to_recv_reqs = TCPServer(self._id, (IP_ETH0, LISTEN_PORT), handle_msg)
		self.server_to_recv_reqs_thread = threading.Thread(target=self.server_to_recv_reqs.serve_forever, daemon=True)
		self.server_to_recv_reqs_thread.start()

	def close(self):
		log(DEBUG, "started")
		self.server_to_recv_reqs_thread.shutdown()
		log(DEBUG, "done")

	def send_to_worker(self, wip, msg):
		msg.src_id = self._id
		msg.src_ip = IP_ETH0
		msg.dst_id = 'w'
		msg.dst_ip = wip
		send_msg(msg)
		log(DEBUG, "sent", wip=wip, msg=msg)

# ***************************  CommerOnClient  *************************** #
class CommerOnClient():
	def __init__(self, _id, handle_msg):
		self._id = _id

		self.server_to_recv_results = TCPServer(self._id, (IP_ETH0, LISTEN_PORT), handle_msg)
		self.server_to_recv_results_thread = threading.Thread(target=self.server_to_recv_results.serve_forever, daemon=True)
		self.server_to_recv_results_thread.start()

		self.mid_ip_m = {}

	def close(self):
		log(DEBUG, "started")
		self.server_to_recv_results_thread.shutdown()
		log(DEBUG, "done")

	def reg(self, mid, mip):
		self.mid_ip_m[mid] = mip

	def send_msg(self, mid, msg):
		check(mid in self.mid_ip_m, "Not registered", mid=mid)
		msg.payload.mid = mid
		msg.src_id = self._id
		msg.src_ip = IP_ETH0
		msg.dst_id = mid
		msg.dst_ip = self.mid_ip_m[mid]
		send_msg(msg)

# ***************************	 CommerOnWorker	 *************************** #
class CommerOnWorker():
	def __init__(self, _id, msg_q):
		self._id = _id
		self.msg_q = msg_q

		self.server_to_recv_reqs = TCPServer(self._id, (IP_ETH0, LISTEN_PORT), self.handle_msg)
		self.server_to_recv_reqs_thread = threading.Thread(target=self.server_to_recv_reqs.serve_forever, daemon=True)
		self.server_to_recv_reqs_thread.start()

		log(DEBUG, "constructed;", self=self)

	def __repr__(self):
		return 'CommerOnWorker(id= {})'.format(self._id)

	def close(self):
		log(DEBUG, "started")
		self.server_to_recv_reqs_thread.shutdown()
		log(DEBUG, "done")

	def handle_msg(self, msg):
		log(DEBUG, "started", msg=msg)
		self.msg_q.put(msg)
		log(DEBUG, "done")

	def send_info(self, msg):
		msg.dst_id = msg.src_id
		msg.dst_ip = msg.src_ip
		msg.src_id = self._id
		msg.src_ip = IP_ETH0
		send_msg(msg)
		log(DEBUG, "sent", msg=msg)

	def send_result(self, msg):
		msg.dst_id = msg.payload.cid
		msg.dst_ip = msg.payload.cip
		msg.src_id = self._id
		msg.src_ip = IP_ETH0
		send_msg(msg)
		log(DEBUG, "sent", msg=msg)
