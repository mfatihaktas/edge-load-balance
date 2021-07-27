import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append('./sim_exploreExploit')
sys.path.append('./sim_podc')

from rvs import *
from debug_utils import *

import sim_exploreExploit.sim as sim_explore
import sim_podc.sim as sim_podc



if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	# log_global_vars()
