#!/usr/bin/env python
##############################################
# The MIT License (MIT)
# Copyright (c) 2016 Kevin Walchko
# see LICENSE for full details
##############################################

from __future__ import print_function
from __future__ import division
# import time
from math import pi
from Quadruped import Quadruped
from Gait import DiscreteRippleGait
from ahrs import AHRS

##########################

"""
This is a simple demo that walks in a pre-defined path
"""


class SimpleQuadruped(Quadruped):
	def __init__(self, data):
		Quadruped.__init__(self, data)
		self.ahrs = AHRS()

		self.robot = Quadruped(data)
		leg = self.robot.legs[0].foot0
		self.crawl = DiscreteRippleGait(45.0, leg)
		self.path = [  # x,y,rot
			[50, 0, 0],
			[50, 0, 0],
			[50, 0, 0],
			[50, 0, 0],
			[50, 0, 0],
			[50, 0, 0],
			[50, 0, 0],
			[50, 0, 0],
			[50, 0, 0],
			[50, 0, 0],
			[0, 0, pi/4],
			[0, 0, pi/4],
			[0, 0, pi/4],
			[0, 0, -pi/4],
			[0, 0, -pi/4],
			[0, 0, -pi/4],
			[-50, 0, 0],
			[-50, 0, 0],
			[-50, 0, 0],
			[-50, 0, 0],
			[-50, 0, 0],
			[-50, 0, 0],
			[-50, 0, 0],
			[-50, 0, 0],
			[-50, 0, 0],
			[-50, 0, 0],
		]

	def run(self):
		# run = True
		# while run:
		for pose in self.path:
			x, y, rz = pose
			leg = self.robot.legs[0].foot0
			cmd = [x, y, rz]
			print('***********************************')
			print('* rest {:.2f} {:.2f} {:.2f}'.format(*leg))
			print('* cmd {:.2f} {:.2f} {:.2f}'.format(*cmd))
			print('***********************************')
			self.crawl.command(cmd, self.robot.moveFoot, steps=12)

			# read ahrs
			d = self.ahrs.read(deg=True)
			print('\n\n<<<<<<<<<<<>>>>>>>>>>>')
			print('ahrs', d)
			print('<<<<<<<<<<<>>>>>>>>>>>\n\n')


def run():
	# angles are always [min, max]
	# xl-320
	test = {
		# 'serialPort': '/dev/serial0',  # real robot
		# 'legLengths': {
		# 	'coxaLength': 45,
		# 	'femurLength': 55,
		# 	'tibiaLength': 104
		# },
		# 'legAngleLimits': [[-90, 90], [-90, 90], [-150, 0]],
		# 'legOffset': [150, 150, 150+90]
	}

	robot = SimpleQuadruped(test)
	robot.run()


if __name__ == "__main__":
	run()