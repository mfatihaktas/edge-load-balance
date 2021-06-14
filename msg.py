import jsonpickle, pprint

class Msg():
	def __init__(self, _id, payload, src_id=None, src_ip=None, dst_id=None, dst_ip=None):
		self._id = _id
		self.payload = payload
		self.src_id = src_id
		self.src_ip = src_ip
		self.dst_id = dst_id
		self.dst_ip = dst_ip

	def __repr__(self):
		return "Msg(id= {} \n\t payload= {} \n\t src_id= {} \n\t src_ip= {} \n\t dst_id= {} \n\t dst_ip= {})".format(self._id, self.payload, self.src_id, self.src_ip, self.dst_id, self.dst_ip)

	def to_str(self):
		return jsonpickle.encode(self)

def msg_from_str(s):
	return jsonpickle.decode(s)

class ConnReq():
	def __init__(self, port_client_listening):
		self.port_client_listening = port_client_listening

		self.size_inBs = 0

	def __repr__(self):
		return "ConnReq(port_client_listening= {})".format(self.port_client_listening)

class ConnReply():
	def __init__(self, port_cluster_listening):
		self.port_cluster_listening = port_cluster_listening

		self.size_inBs = 0

	def __repr__(self):
		return "ConnReply(port_cluster_listening= {})".format(self.port_cluster_listening)

class Payload():
	def __init__(self, _id, typ, size_inBs):
		self._id = _id
		self.typ = typ
		self.size_inBs = size_inBs

	def is_req(self):
		return self.typ == 'r'

	def is_result(self):
		return self.typ == 's'

	def is_info(self):
		return self.typ == 'i'

class Info(Payload):
	def __init__(self, _id, m):
		super().__init__(_id, 'i', size_inBs=0)
		self.m = m

	def __repr__(self):
		return "Info(m=\n {})".format(pprint.pformat(self.m))

class ReqRes(Payload):
	def __init__(self, _id, typ, size_inBs, cid, cip, serv_time=None, probe=False):
		super().__init__(_id, typ, size_inBs)
		self.cid = cid
		self.cip = cip
		self.serv_time = serv_time
		self.probe = probe

		self.epoch_departed_client = None
		self.epoch_arrived_cluster = None
		self.epoch_departed_cluster = None
		self.epoch_arrived_client = None

	def __hash__(self):
		return hash((self._id, self.cid))

	def __eq__(self, other):
		return (self._id, self.cid) == (other._id, other.cid)

class Request(ReqRes):
	def __init__(self, _id, size_inBs, cid, cip, serv_time):
		super().__init__(_id, 'r', size_inBs, cid, cip, serv_time)

	def __repr__(self):
		return "Request(id= {}, cid= {}, size_inBs= {}, serv_time= {}, probe= {})".format(self._id, self.cid, self.size_inBs, self.serv_time, self.probe)

class Result(ReqRes):
	def __init__(self, _id, cid, cip, size_inBs=0):
		super().__init__(_id, 's', size_inBs, cid, cip)

	def __repr__(self):
		return "Result(id= {}, cid= {}, probe= {})".format(self._id, self.cid, self.probe)

def result_from_req(req):
	r = Result(req._id, req.cid, req.cip)

	r.serv_time = req.serv_time
	r.probe = req.probe
	r.epoch_departed_client = req.epoch_departed_client
	r.epoch_arrived_cluster = req.epoch_arrived_cluster
	r.epoch_departed_cluster = req.epoch_departed_cluster
	r.epoch_arrived_client = req.epoch_arrived_client
	return r
