import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy, random

from debug_utils import *
from priority_dict import *

class Ball():
	def __init__(self, _id, rest_time):
		self._id = _id
		self.rest_time = rest_time

		self.epoch_cost_l = []

	def __repr__(self):
		return "Ball(id= {})".format(self._id)

class BallGen():
	def __init__(self, env, m, rest_time_rv, num_balls_to_gen, out=None):
		self.env = env
		self.m = m
		self.rest_time_rv = rest_time_rv
		self.num_balls_to_gen = num_balls_to_gen
		self.out = out

		self.ball_id_to_gen_s = simpy.Store(env)

		for i in range(self.m):
			self.ball_id_to_gen_s.put(i)

		self.act = env.process(self.run())

	def __repr__(self):
		return "BallGen(m= {})".format(self.m)

	def put(self, bid):
		slog(DEBUG, self.env, self, "recved back", bid=bid)
		self.ball_id_to_gen_s.put(bid)

	def run(self):
		slog(DEBUG, self.env, self, "started", num_balls_to_gen=self.num_balls_to_gen)

		for _ in range(self.num_balls_to_gen):
			bid = yield self.ball_id_to_gen_s.get()

			b = Ball(bid, self.rest_time_rv.sample())
			self.out.put(b)

		slog(DEBUG, self.env, self, "done")

class Bin():
	def __init__(self, _id, env, out=None):
		self._id = _id
		self.env = env
		self.out = out

		self.ball_id__exp_epoch_heap_m = priority_dict()

		self.ball_token_s = simpy.Store(env)
		self.interrupt = None
		self.got_interrupted = False

		self.act = env.process(self.run())

	def __repr__(self):
		return "Bin(id= {})".format(self._id)

	def height(self):
		return len(self.ball_id__exp_epoch_heap_m)

	def put(self, ball):
		slog(DEBUG, self.env, self, "recved", ball=ball)
		check(ball._id not in self.ball_id__exp_epoch_heap_m, "Only one copy should exist for each ball at all times")

		self.ball_id__exp_epoch_heap_m[ball._id] = self.env.now + ball.rest_time
		self.ball_token_s.put(1)

		if self.got_interrupted is False and self.interrupt is not None:
			self.got_interrupted = True
			self.interrupt.succeed()

	def run(self):
		slog(DEBUG, self.env, self, "started")

		while True:
			yield self.ball_token_s.get()

			bid = self.ball_id__exp_epoch_heap_m.smallest()
			self.interrupt = self.env.event()
			t = self.ball_id__exp_epoch_heap_m[bid] - self.env.now
			slog(DEBUG, self.env, self, "waiting", bid=bid, t=t)
			yield (self.interrupt | self.env.timeout(t))

			if self.got_interrupted:
				slog(DEBUG, self.env, self, "got interrupted", bid=bid)
				self.interrupt = None
				self.got_interrupted = False
				self.ball_token_s.put(1)
			else:
				self.ball_id__exp_epoch_heap_m.pop(bid)
				self.out.put(bid)

		slog(DEBUG, self.env, self, "done")

class Bin_fluctuating(Bin):
	def __init__(self, _id, env, slow_dur_rv, normal_dur_rv, out=None):
		super().__init__(_id, env, out)
		self.slow_dur_rv = slow_dur_rv
		self.normal_dur_rv = normal_dur_rv

		self.state = 'n' # 's'
		self.mult_height_factor = 1

		self.act = env.process(self.run_fluctuating_state())

	def height(self):
		return super().height() * self.mult_height_factor

	def __repr__(self):
		return "Bin_fluctuating(id= {})".format(self._id)

	def run_fluctuating_state(self):
		slog(DEBUG, self.env, self, "started")

		while True:
			if self.state == 'n':
				self.mult_height_factor = 1
				dur = self.normal_dur_rv.sample()
				slog(DEBUG, self.env, self, "normal state started", dur=dur)
				yield self.env.timeout(dur)

				self.state = 's'
			elif self.state == 's':
				self.mult_height_factor = 10
				dur = self.slow_dur_rv.sample()
				slog(DEBUG, self.env, self, "slow state started", dur=dur)
				yield self.env.timeout(dur)

				self.state = 'n'

class BinCluster():
	def __init__(self, env, n, d, ball_restime_rv, ball_gen, frac_fluctuating=0, slow_dur_rv=None, normal_dur_rv=None):
		self.env = env
		self.n = n
		self.d = d
		self.ball_restime_rv = ball_restime_rv

		ball_gen.out = self

		nf = int(frac_fluctuating * n)
		self.bin_l = [Bin_fluctuating('bin-{}'.format(i), env, slow_dur_rv, normal_dur_rv) for i in range(nf)]
		for i in range(nf, n):
			self.bin_l.append(Bin('bin-{}'.format(i), env))

		for b in self.bin_l:
			b.out = ball_gen

		self.ball_s = simpy.Store(env)
		self.act = env.process(self.run())

		self.epoch_I_l = []

	def __repr__(self):
		return "BinCluster(n= {}, d= {})".format(self.n, self.d)

	def put(self, ball):
		slog(DEBUG, self.env, self, "recved", ball=ball)
		self.ball_s.put(ball)

	def record_state(self):
		num_balls = 0
		max_height = 0
		for b in self.bin_l:
			h = b.height()
			num_balls += h
			max_height = max(h, max_height)
		I = max_height / (num_balls / len(self.bin_l))
		self.epoch_I_l.append((self.env.now, I))
		slog(DEBUG, self.env, self, "recorded", I=I)

	def run(self):
		while True:
			ball = yield self.ball_s.get()

			bin_l = random.sample(self.bin_l, self.d)
			h_i_l = [(b.height(), i) for i, b in enumerate(bin_l)]
			bin_ = bin_l[min(h_i_l)[1]]
			slog(DEBUG, self.env, self, "assigning", ball=ball, bin_=bin_)
			bin_.put(ball)

			self.record_state()
