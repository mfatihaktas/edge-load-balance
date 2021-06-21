import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import pprint

from flask import Flask, request, render_template
from server import DashboardServer
from debug_utils import *

app = Flask(__name__, static_url_path='', static_folder='static', template_folder='static')

@app.route('/', methods=['GET'])
def index():
	img_filename_l = os.listdir('static/image')
	log(DEBUG, "", img_filename_l=img_filename_l)
	img_path_l = ['image/' + name for name in img_filename_l]
	# log(DEBUG, "", img_path_l=img_path_l)

	app.logger.info("Returning index.html")
	return render_template("index.html",
												 img_path_l=img_path_l)

if __name__ == '__main__':
	server = DashboardServer()

	app.run(host='0.0.0.0', port=5001) # debug=True
