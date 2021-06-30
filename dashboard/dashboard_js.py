import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import pprint, getopt

from flask import Flask, request, render_template
from server import DashboardServer
from debug_utils import *

app = Flask(__name__, static_url_path='', static_folder='static', template_folder='static')

@app.route('/', methods=['GET'])
def index():
	img_filename_l = os.listdir('dashboard/static/image')
	img_filename_l.sort()
	log(DEBUG, "", img_filename_l=img_filename_l)

	c_img_path_l = ['image/' + filename for filename in img_filename_l if '_c_' in filename]
	m_img_path_l = ['image/' + filename for filename in img_filename_l if '_m_' in filename]
	# log(DEBUG, "", img_path_l=img_path_l)

	app.logger.info("Returning index_js.html")
	return render_template("index_js.html", m_img_path_l=m_img_path_l, c_img_path_l=c_img_path_l)

def parse_argv(argv):
	m = {}
	try:
		opts, args = getopt.getopt(argv, '', ['log_to_std='])
	except getopt.GetoptError:
		assert_("Wrong args;", opts=opts, args=args)

	for opt, arg in opts:
		if opt == '--log_to_std':
			m['log_to_std'] = bool(int(arg))
		else:
			assert_("Unexpected opt= {}, arg= {}".format(opt, arg))

	if 'log_to_std' not in m:
		m['log_to_std'] = True

	return m

if __name__ == '__main__':
	m = parse_argv(sys.argv[1:])
	log_to_file('d.log')
	if m['log_to_std']:
		log_to_std()

	server = DashboardServer()

	app.run(host='0.0.0.0', port=5001) # debug=True
