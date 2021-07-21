import enum

class Request():
	def __init__(self, _id, src_id, dst_id, serv_time):
		self._id = _id
		self.src_id = src_id
		self.dst_id = dst_id
		self.serv_time = serv_time

		self.epoch_departed_client = None
		self.epoch_arrived_net = None
		self.epoch_arrived_cluster = None
		self.epoch_started_service = None
		self.epoch_departed_cluster = None
		self.epoch_arrived_client = None

		self.num_server_share = None

	def __repr__(self):
		return "Request(id= {}, src_id= {}, dst_id= {}, serv_time= {})".format(self._id, self.src_id, self.dst_id, self.serv_time)

class Msg():
	def __init__(self, _id, payload, src_id=None, dst_id=None):
		self._id = _id
		self.payload = payload
		self.src_id = src_id
		self.dst_id = dst_id

	def __repr__(self):
		return "Msg(id= {} \n\t payload= {} \n\t src_id= {} \n\t dst_id= {})".format(self._id, self.payload, self.src_id, self.dst_id)

class Payload():
	def __init__(self, _id, p_typ):
		self._id = _id
		self.p_typ = p_typ

	def is_req(self):
		return self.p_typ == 'r'

	def is_result(self):
		return self.p_typ == 's'

	def is_info(self):
		return self.p_typ == 'i'

	def is_update(self):
		return self.p_typ == 'u'

class InfoType(enum.Enum):
	client_disconn = 1
	worker_req_completion = 2

class Info(Payload):
	def __init__(self, _id, typ: InfoType):
		super().__init__(_id, 'i')
		self.typ = typ

	def __repr__(self):
		return "Info(typ= {})".format(self.typ.name)

class ReqRes(Payload):
	def __init__(self, _id, p_typ, cid, serv_time=None, probe=False):
		super().__init__(_id, p_typ)
		self.cid = cid
		self.serv_time = serv_time
		self.probe = probe

		self.cl_id = None
		self.epoch_departed_client = None
		self.epoch_arrived_cluster = None
		self.epoch_departed_cluster = None
		self.epoch_arrived_client = None

	def __hash__(self):
		return hash((self._id, self.cid))

	def __eq__(self, other):
		return (self._id, self.cid) == (other._id, other.cid)

class Request(ReqRes):
	def __init__(self, _id, cid, serv_time):
		super().__init__(_id, 'r', cid, serv_time)

	def __repr__(self):
		return "Request(id= {}, cid= {}, cl_id= {}, serv_time= {}, probe= {})".format(self._id, self.cid, self.cl_id, self.serv_time, self.probe)

class Result(ReqRes):
	def __init__(self, _id, cid):
		super().__init__(_id, 's', cid)

	def __repr__(self):
		return "Result(id= {}, cid= {}, cl_id= {}, probe= {})".format(self._id, self.cid, self.cl_id, self.probe)

def result_from_req(req):
	r = Result(req._id, req.cid)

	r.cl_id = req.cl_id
	r.serv_time = req.serv_time
	r.probe = req.probe
	r.epoch_departed_client = req.epoch_departed_client
	r.epoch_arrived_cluster = req.epoch_arrived_cluster
	r.epoch_departed_cluster = req.epoch_departed_cluster
	r.epoch_arrived_client = req.epoch_arrived_client
	return r
