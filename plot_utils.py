import matplotlib
# matplotlib.rcParams['pdf.fonttype'] = 42
# matplotlib.rcParams['ps.fonttype'] = 42
# matplotlib.use('Agg')

# import mpld3
# mpld3.enable_notebook()

import matplotlib.pyplot as plot
import itertools, scipy, json
import numpy as np

from debug_utils import *

NICE_BLUE = '#66b3ff'
NICE_RED = '#ff9999'
NICE_GREEN = '#99ff99'
NICE_ORANGE = '#ffcc99'
NICE_PURPLE = 'mediumpurple'

nice_color = itertools.cycle((NICE_BLUE, NICE_RED, NICE_GREEN, NICE_ORANGE))
dark_color = itertools.cycle(('green', 'purple', 'blue', 'magenta', 'purple', 'gray', 'brown', 'turquoise', 'gold', 'olive', 'silver', 'rosybrown', 'plum', 'goldenrod', 'lightsteelblue', 'lightpink', 'orange', 'darkgray', 'orangered'))
light_color = itertools.cycle(('silver', 'rosybrown', 'plum', 'lightsteelblue', 'lightpink', 'orange', 'turquoise'))
linestyle = itertools.cycle(('-', '--', '-.', ':') )
marker_cycle = itertools.cycle(('x', '+', 'v', '^', 'p', 'd', '<', '>', '1' , '2', '3', '4') )
skinny_marker_l = ['x', '+', '1', '2', '3', '4']

mew, ms = 1, 2 # 3, 5

def prettify(ax):
	ax.patch.set_alpha(0.2)
	ax.spines['right'].set_visible(False)
	ax.spines['top'].set_visible(False)

def area_under_cdf(l, xl, xu):
	x_l = sorted(l)
	y_l = np.arange(len(x_l) )/len(x_l)

	il = 0
	while x_l[il] < xl: il += 1
	iu = 0
	while x_l[iu] < xu: iu += 1
	return np.trapz(y=y_l[il:iu], x=x_l[il:iu] )

def avg_within(x_l, xl, xu):
	return np.mean([x for x in x_l if x >= xl and x <= xu] )

def CDFval_atx_l(l, atx_l):
	x_l = sorted(l)
	y_l = np.arange(len(x_l) )/len(x_l)

	def val_atx(x):
		i = 0
		while x_l[i] < x: i += 1
		return y_l[i]

	return {x: val_atx(x) for x in atx_l}

def add_pdf(l, label, color, bins=50):
	# w_l = np.ones_like(l)/float(len(l) )
	# plot.hist(l, bins=bins, weights=w_l, label=label, color=color, edgecolor='black')

	# n = len(l)//bins
	# p, x = np.histogram(l, bins=n) # bin it into n = N//10 bins
	# x = x[:-1] + (x[1] - x[0])/2	 # convert bin edges to centers
	# f = scipy.interpolate.UnivariateSpline(x, p, s=n)
	# plot.plot(x, f(x), label=label, color=color, ls='--', lw=2, mew=2, ms=2)

	# density = scipy.stats.gaussian_kde(l)
	# # xs = np.linspace(0, 8, 200)
	# density.covariance_factor = lambda : .25
	# density._compute_covariance()
	# plot.plot(l, density(l) )

	seaborn.distplot(l, hist=False, norm_hist=True, kde=True, bins=bins, label=label, color=color,
		hist_kws={'edgecolor':'black'}, kde_kws={'linewidth': 3} )

def add_cdf(l, ax, label, color, drawline_x_l=[] ):
	if l is None:
		return

	plot.sca(ax)
	x_l = sorted(l)
	y_l = np.arange(len(x_l))/len(x_l)
	plot.plot(x_l, y_l, label=label, color=color, marker='.', linestyle=':', lw=2, mew=2, ms=2) # lw=1, mew=1, ms=1

	def drawline(x, c=color, ls='-'):
		i = 0
		while i < len(x_l) and x_l[i] < x: i += 1
		if i == len(x_l):
			return
		ax.add_line(
			matplotlib.lines.Line2D([x_l[i], x_l[i]], [0, y_l[i]], color=c, linestyle=ls))
		ax.add_line(
			matplotlib.lines.Line2D([0, x_l[i]], [y_l[i], y_l[i]], color=c, linestyle=ls))

	for x in drawline_x_l:
		drawline(x)

	mean = np.mean(l)
	# std = np.std(l)
	drawline(mean, ls=':')
	# drawline(mean - std, c='k', ls='--')
	# drawline(mean + std, c='k', ls='--')

def ylabel(resource, metric):
  if resource == 'cpu' and metric == 'usage':
    return 'CPU usage (Core)'
  elif resource == 'memory' and metric == 'current':
    return 'Memory usage (GB)'
  else:
    log(ERROR, "Unrecognized args;", resource=resource, metric=metric)
    return -1

def colorbar(mappable):
  from mpl_toolkits.axes_grid1 import make_axes_locatable
  last_axes = plot.gca()
  ax = mappable.axes
  fig = ax.figure
  divider = make_axes_locatable(ax)
  cax = divider.append_axes("right", size="5%", pad=0.05)
  cbar = fig.colorbar(mappable, cax=cax)
  plot.sca(last_axes)
  return cbar

def plot_cdf(rv, ax, label, color, max_=None, drawline_x_l=[]):
	plot.sca(ax)
	if max_ is None:
		max_ = rv.u
	x_l = np.linspace(rv.l, max_, 100)
	y_l = [rv.cdf(x) for x in x_l]
	plot.plot(x_l, y_l, label=label, color=color, marker='.', linestyle=':', lw=2, mew=2, ms=2) # lw=1, mew=1, ms=1

# TODO: Move file utils below to a file_utils.py
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

## Got ZoomPan from
## https://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel
def zoom_factory(ax, base_scale = 2.):
	def zoom_fun(event):
		# get the current x and y limits
		cur_xlim = ax.get_xlim()
		cur_ylim = ax.get_ylim()
		cur_xrange = (cur_xlim[1] - cur_xlim[0])*.5
		cur_yrange = (cur_ylim[1] - cur_ylim[0])*.5
		xdata = event.xdata # get event x location
		ydata = event.ydata # get event y location
		if event.button == 'up':
			# deal with zoom in
			scale_factor = 1/base_scale
		elif event.button == 'down':
			# deal with zoom out
			scale_factor = base_scale
		else:
			# deal with something that should never happen
			scale_factor = 1
			# print event.button
		# set new limits
		ax.set_xlim([xdata - cur_xrange*scale_factor,
								 xdata + cur_xrange*scale_factor])
		ax.set_ylim([ydata - cur_yrange*scale_factor,
								 ydata + cur_yrange*scale_factor])
		plot.draw() # force re-draw

	fig = ax.get_figure() # get the figure of interest
	# attach the call back
	fig.canvas.mpl_connect('scroll_event',zoom_fun)

	#return the function
	return zoom_fun

def exp_zoom_pan():
	import random

	x_l = list(range(1000))
	y_l = [random.randint(0, 10) for _ in range(len(x_l))]

	plot.plot(x_l, y_l, color=next(nice_color), marker='x', linestyle='None', lw=2, mew=3, ms=5)
	f = zoom_factory(plot.gca(), base_scale=1.5)

	plot.show()

if __name__ == '__main__':
	exp_zoom_pan()
