import jsonpickle, pprint, enum

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

class Payload():
	def __init__(self, _id, p_typ, size_inBs):
		self._id = _id
		self.p_typ = p_typ
		self.size_inBs = size_inBs

	def is_req(self):
		return self.p_typ == 'r'

	def is_result(self):
		return self.p_typ == 's'

	def is_info(self):
		return self.p_typ == 'i'

	def is_update(self):
		return self.p_typ == 'u'

class UpdateType(enum.Enum):
	from_client = 1
	from_master = 2
	from_worker = 3

class Update(Payload):
	def __init__(self, _id, typ: UpdateType, m):
		super().__init__(_id, 'u', size_inBs=0)
		self.typ = typ

		self.m = m

	def __repr__(self):
		return "Update(typ= {}, \n\t m=\n {})".format(self.typ.name, pprint.pformat(self.m))

class InfoType(enum.Enum):
	client_disconn = 1
	worker_req_completion = 2
	close = 3

class Info(Payload):
	def __init__(self, _id, typ: InfoType):
		super().__init__(_id, 'i', size_inBs=0)
		self.typ = typ

	def __repr__(self):
		return "Info(typ= {})".format(self.typ.name)

class ReqRes(Payload):
	def __init__(self, _id, p_typ, size_inBs, cid, cip, serv_time=None, probe=False):
		super().__init__(_id, p_typ, size_inBs)
		self.cid = cid
		self.cip = cip
		self.serv_time = serv_time
		self.probe = probe

		self.mid = None
		self.mip = None
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
		return "Request(id= {}, cid= {}, mid= {}, size_inBs= {}, serv_time= {}, probe= {})".format(self._id, self.cid, self.mid, self.size_inBs, self.serv_time, self.probe)

class Result(ReqRes):
	def __init__(self, _id, cid, cip, size_inBs=0):
		super().__init__(_id, 's', size_inBs, cid, cip)

	def __repr__(self):
		return "Result(id= {}, cid= {}, mid= {}, probe= {})".format(self._id, self.cid, self.mid, self.probe)

def result_from_req(req):
	r = Result(req._id, req.cid, req.cip)

	r.serv_time = req.serv_time
	r.probe = req.probe
	r.mid = req.mid
	r.mip = req.mip
	r.epoch_departed_client = req.epoch_departed_client
	r.epoch_arrived_cluster = req.epoch_arrived_cluster
	r.epoch_departed_cluster = req.epoch_departed_cluster
	r.epoch_arrived_client = req.epoch_arrived_client
	return r
