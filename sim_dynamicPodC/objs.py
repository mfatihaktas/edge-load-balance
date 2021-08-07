import os, sys
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import simpy

from debug_utils import *
from priority_dict import *

class Ball():
	def __init__(self, _id, rest_time):
		self._id = _id
		self.rest_time = rest_time

	def __repr__(self):
		return "Ball(id= {})".format(self._id)

class BallGen():
	def __init__(self, env, m, rest_time_rv, num_balls_to_gen, out):
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

class PodCScher():
	def __init__(self, env, d, bin_l):
		self.d = d
		self.bin_l = bin_l

		self.ball_s = simpy.Store(env)
		self.act = env.process(self.run())

	def __repr__(self):
		return "PodCScher(d= {})".format(self.d)

	def put(self, ball):
		slog(DEBUG, self.env, self, "recved", ball=ball)
		self.ball_s.put(ball)

	def run(self):
		while True:
			ball = yield self.ball_s.get()

			bin_l = random.sample(self.bin_l, self.d)
			h_i_l = [(b.height(), i) for i, b in enumerate(bin_l)]
			bin_ = bin_l[min(h_i_l)[1]]
			slog(DEBUG, self.env, self, "assigning", ball=ball, bin_=bin_)
			bin_.put(ball)

class Bin():
	def __init__(self, _id, env, out):
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

	def put(self, ball):
		slog(DEBUG, self.env, self, "recved", ball=ball)
		check(ball._id not in self.ball_id__exp_epoch_heap_m, "Only one copy should exist for each ball at all times")

		self.ball_id__exp_epoch_heap_m[ball._id] = self.env.now + ball.rest_time
		self.ball_token_s.put(1)

		if self.interrupt is not None:
			self.got_interrupted = True
			self.interrupt.succeed()

	def run(self):
		while True:
			yield self.ball_token_s.get()

			bid = self.ball_id__exp_epoch_heap_m.smallest()
			self.interrupt = self.env.event()
			t = self.ball_id__exp_epoch_heap_m[bid] - self.env.now
			slog(DEBUG, self.env, self, "waiting", bid=bid, t=t)
			yield (self.interrupt | self.env.timeout(t))

			if self.got_interrupted:
				slog(DEBUG, self.env, self, "got interrupted", bid=bid)
				self.got_interrupted = False
				self.interrupt = None
				self.ball_token_s.put(1)
			else:
				self.ball_id__exp_epoch_heap_m.pop(bid)
				self.out.put(bid)

		slog(DEBUG, self.env, self, "done")
