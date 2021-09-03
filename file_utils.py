import json

from debug_utils import *

def write_to_file(data, fname):
	with open(fname, 'w') as f:
		f.write(data)
		log(INFO, "done", fname=fname)

def read_from_file(fname):
	d = None
	try:
		with open(fname, 'r') as f:
			d = f.read()
			log(INFO, "done", fname=fname)
	except FileNotFoundError:
		log(WARNING, "File not found", fname=fname)
	return d

def read_json_from_file(fname):
	d = None
	try:
		with open(fname) as f:
			d = json.load(f)
			log(INFO, "done", fname=fname)
	except FileNotFoundError:
		log(WARNING, "File not found", fname=fname)
	return d
