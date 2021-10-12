import sim_config
from file_utils import *
from debug_utils import *

def gen_inter_gen_time_list(ci, inter_gen_time_rv, num_req_to_finish):
	import os.path

	filename = sim_config.get_inter_req_gen_time_filename(ci, inter_gen_time_rv, num_req_to_finish)
	log(WARNING, "", ci=ci, filename=filename, num_req_to_finish=num_req_to_finish)

	if os.path.exists(filename):
		log(WARNING, "Already exists", filename=filename)
		return

	inter_gen_time_l = []
	for _ in range(10 * num_req_to_finish):
		inter_gen_time_l.append(inter_gen_time_rv.sample())

	write_to_file(json.dumps(inter_gen_time_l), filename)

def bootstrap_inter_gen_time_list():
	for ci in range(sim_config.m):
		log(WARNING, "> ci= {}".format(ci))

		for ro in sim_config.RO_l:
			log(WARNING, "ro= {}".format(ro))
			inter_gen_time_rv = sim_config.get_inter_req_gen_time_rv(ro)
			gen_inter_gen_time_list(ci, inter_gen_time_rv, sim_config.num_req_to_finish)

	log(DEBUG, "done.", inter_gen_time_rv=inter_gen_time_rv, num_req_to_finish=sim_config.num_req_to_finish)

if __name__ == '__main__':
	log_to_std()

	bootstrap_inter_gen_time_list()
