import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from rvs import *
from debug_utils import *

## m: # balls
## n: # bins
def sim_EmaxHeight_wGaussianNoise(m, n, d, coeff_var, num_exp):
	log(DEBUG, "started", m=m, n=n, d=d, coeff_var=coeff_var, num_exp=num_exp)

	def single_exp():
		bin_l = [0] * n
		for i in range(m):
			bi_l = random.sample(range(n), d)
			log(DEBUG, "", bi_l=bi_l)
			if d == 1:
				bi = bi_l[0]
			else:
				b_i_l = []
				for j in bi_l:
					mu = bin_l[j]
					h_rv = Normal(mu, coeff_var * mu)
					h = max(h_rv.sample(), 0)
					b_i_l.append((h, j))
				b_i_l.sort()
				bi = b_i_l[2][1]
			bin_l[bi] += 1
		return max(bin_l)

	cum_max_height = 0
	for i in range(num_exp):
		max_height = single_exp()
		log(DEBUG, "Exp-{}".format(i), max_height=max_height)
		cum_max_height += max_height
	return cum_max_height / num_exp

def sim_EmaxHeight_wAdditiveNoise(m, n, d, noise_rv, num_exp):
	log(DEBUG, "started", m=m, n=n, d=d, noise_rv=noise_rv, num_exp=num_exp)

	def single_exp():
		bin_l = [0] * n
		for i in range(m):
			bi_l = random.sample(range(n), d)
			log(DEBUG, "", bi_l=bi_l)
			if d == 1:
				bi = bi_l[0]
			else:
				b_i_l = []
				for j in bi_l:
					h = max(bin_l[j] + noise_rv.sample(), 0)
					b_i_l.append((h, j))
				bi = min(b_i_l)[1]
			bin_l[bi] += 1
		return max(bin_l)

	cum_max_height = 0
	for i in range(num_exp):
		max_height = single_exp()
		log(DEBUG, "Exp-{}".format(i), max_height=max_height)
		cum_max_height += max_height
	return cum_max_height / num_exp

## I: max-height / min-max-height
def plot_EI_vs_d(n):
	log(INFO, "started", n=n)
	m = 10 * n
	num_exp = 1 # 3 # 1000

	def plot_wAdditiveNoise(max_noise_factor):
		log(INFO, "started", max_noise_factor=max_noise_factor)
		max_noise = max_noise_factor * m / n
		noise_rv = DUniform(l=-max_noise, u=max_noise)

		d_l, EI_l = [], []
		for d in [1, 2, 3, 10]:
			d_l.append(d)

			E_max_height = sim_EmaxHeight_wAdditiveNoise(m, n, d, noise_rv, num_exp)
			EI = E_max_height / (m / n)
			log(INFO, ">>", d=d, EI=EI)
			EI_l.append(EI)
		plot.plot(d_l, EI_l, color=next(dark_color), label=r'$f= {}$'.format(max_noise_factor), marker=next(marker_cycle), linestyle=next(linestyle), lw=2, mew=3, ms=5)

	def plot_wGaussianNoise(coeff_var):
		log(INFO, "started", coeff_var=coeff_var)

		d_l, EI_l = [], []
		for d in [1, 2, 3, 10]:
			d_l.append(d)

			E_max_height = sim_EmaxHeight_wGaussianNoise(m, n, d, coeff_var, num_exp)
			EI = E_max_height / (m / n)
			log(INFO, ">>", d=d, EI=EI)
			EI_l.append(EI)
		plot.plot(d_l, EI_l, color=next(dark_color), label='CV= {}'.format(coeff_var), marker=next(marker_cycle), linestyle=next(linestyle), lw=2, mew=3, ms=5)

	# plot_wAdditiveNoise(max_noise_factor = 0)
	# plot_wAdditiveNoise(max_noise_factor = 0.5)
	# plot_wAdditiveNoise(max_noise_factor = 1)
	# plot_wAdditiveNoise(max_noise_factor = 2)
	# plot_wAdditiveNoise(max_noise_factor = 3)

	plot_wGaussianNoise(coeff_var = 0.2)
	plot_wGaussianNoise(coeff_var = 0.5)
	plot_wGaussianNoise(coeff_var = 1)
	plot_wGaussianNoise(coeff_var = 2)
	plot_wGaussianNoise(coeff_var = 3)

	fontsize = 14
	plot.legend(fontsize=fontsize)
	plot.ylabel(r'$E[I]$', fontsize=fontsize)
	plot.xlabel(r'$d$', fontsize=fontsize)
	plot.title(r'$n= {}$, $m= {}$'.format(n, m))
	plot.gcf().set_size_inches(6, 4)
	plot.savefig("plot_EI_vs_d_n_{}.png".format(n), bbox_inches='tight')
	plot.gcf().clear()

	log(DEBUG, "done")

if __name__ == '__main__':
	log_to_std()
	log_to_file('sim.log')

	plot_EI_vs_d(n=500)
