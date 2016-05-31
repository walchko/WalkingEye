#!/usr/bin/env python
#
# Kevin J. Walchko 13 Oct 2014
#
# see http://zeromq.org for more info

import zmq
import json
import numpy
import datetime as dt
import base64
import socket as Socket


class ZMQError(Exception):
	pass


class Base:  # FIXME: 20160525 move printing statements to logging instead?
	"""
	Base class for other derived pub/sub/service classes
	"""
	def __init__(self):
		# functions
		self.ctx = zmq.Context()

		# self.poller = zmq.Poller()

	def zmq_version(self):
		"""
		What version of the zmq (C++) library is python tied to?
		"""
		print('Using ZeroMQ version: %s' % (zmq.version_info()))

	def _stop(self, msg='some pub/sub/srvc'):
		"""
		Internal function, don't call
		"""
		self.ctx.term()
		print '[<] shutting down', msg


class Pub(Base):
	"""
	Simple publisher
	"""
	def __init__(self, bind_to=('localhost', 9000)):
		Base.__init__(self)
		if bind_to[0] == 'localhost':  # do I need to do this?
			bind_to = (Socket.gethostbyname(Socket.gethostname()), bind_to[1])
		self.bind_to = 'tcp://' + bind_to[0] + ':' + str(bind_to[1])

		try:
			self.socket = self.ctx.socket(zmq.PUB)
			self.socket.bind(self.bind_to)

		except Exception, e:
			error = '[-] Pub Error, %s' % (str(e))
			# print error
			raise ZMQError(error)

		# self.poller.register(self.socket, zmq.POLLOUT)

	def __del__(self):
		# self.poller.register(self.socket)
		self.socket.close()
		# self._stop('PUB:' + self.bind_to)

	def pub(self, topic, msg):
		"""
		It appears the send_json() doesn't work for pub/sub.
		in: topic, message
		out: none
		"""
		jmsg = json.dumps(msg)
		self.socket.send_multipart([topic, jmsg])
		# self.socket.send_json(msg)


class Sub(Base):
	"""
	Simple subscriber
	"""
	def __init__(self, topics=None, connect_to=('localhost', 9000), poll_time=0.01):
		Base.__init__(self)
		self.connect_to = 'tcp://' + connect_to[0] + ':' + str(connect_to[1])
		self.poll_time = poll_time
		try:
			self.socket = self.ctx.socket(zmq.SUB)
			self.socket.connect(self.connect_to)
			self.socket.poll(self.poll_time, zmq.POLLIN)

			# manage subscriptions
			if topics is None:
				print "Receiving messages on ALL topics..."
				self.socket.setsockopt(zmq.SUBSCRIBE, '')
			else:
				print "Receiving messages on topics: %s ..." % topics
				for t in topics:
					self.socket.setsockopt(zmq.SUBSCRIBE, t)

		except Exception, e:
			error = '[-] Sub Error, %s' % (str(e))
			# print error
			raise ZMQError(error)

	def __del__(self):
		self.socket.close()
		# self._stop('SUB:' + self.connect_to)

	def recv(self):
		# check to see if there is read, write, or erros
		r, w, e = zmq.select([self.socket], [], [], self.poll_time)

		topic = ''
		msg = {}

		# should this be a for loop? I don't think so???
		if len(r) > 0:
			topic, jmsg = r[0].recv_multipart()
			msg = json.loads(jmsg)

		# topic, jmsg = self.socket.recv_multipart()
		# msg = json.loads(jmsg)
		return topic, msg


class PubBase64(Pub):
	"""
	Publishes info in base64, used for images. The expectation is the user
	compresses the image with jpeg, png, or whatever prior to sending the
	image with this.
	"""
	def __init__(self, bind_to=('localhost', 9000)):
		Pub.__init__(self, bind_to)

	def __del__(self):
		self.socket.close()
		self._stop('PUB_Base64:' + self.bind_to)

	def pub(self, topic, jpeg):
		# JPEG compress frame
		# jpeg = cv2.imencode('.jpg',frame)[1]

		# encode binary into base64 ascii
		b64 = base64.b64encode(jpeg)
		# print 'Frame JPG Base64 size: '+str(len(b64))
		# self.logger.debug('Frame Base64 size: '+str(len(b64)))

		# create a message
		msg = {
			'header': dt.datetime.now(),
			'image': b64
		}

		# serialize it using JSON
		jmsg = json.dumps(msg)

		# send it
		self.socket.send_multipart([topic, jmsg])


class SubBase64(Sub):
	"""
	Subscribes to topics that are encoded in base64, usually images
	"""
	def __init__(self, topics='', connect_to=('localhost', 9000), poll_time=0.01):
		Sub.__init__(self, topics, connect_to, poll_time)

	def __del__(self):
		self.socket.close()
		self._stop('SUB_Base64:' + self.connect_to)

	def recv(self):
		# check to see if there is read, write, or errors
		r, w, e = zmq.select([self.socket], [], [], self.poll_time)

		topic = ''
		msg = {}

		# is there something?
		if len(r) > 0:
			# grab message and topic
			topic, jmsg = r[0].recv_multipart()

			# de-serialize
			msg = json.loads(jmsg)

			# decode base64
			if 'image' in msg:
				im = msg['image']
				im = base64.b64decode(im)
				im = numpy.fromstring(im, dtype=numpy.uint8)
				msg['image'] = im

		return topic, msg


class ServiceProvider(Base):
	"""
	Provides a service
	"""
	def __init__(self, bind_to):
		Base.__init__(self)
		self.socket = self.ctx.socket(zmq.REP)
		tcp = 'tcp://' + bind_to[0] + ':' + str(bind_to[1])
		self.socket.bind(tcp)

	def __del__(self):
		self.socket.close()
		# self._stop('Srvc:'+ self.bind_to)

	def listen(self, callback):
		# print 'listen'
		while True:
			jmsg = self.socket.recv()
			msg = json.loads(jmsg)

			ans = callback(msg)

			jmsg = json.dumps(ans)
			self.socket.send(jmsg)


class ServiceClient(Base):
	"""
	Client socket to get a response back from a service provider
	"""
	def __init__(self, bind_to):
		Base.__init__(self)
		self.socket = self.ctx.socket(zmq.REQ)
		tcp = 'tcp://' + bind_to[0] + ':' + str(bind_to[1])
		self.socket.connect(tcp)

	def __del__(self):
		self.socket.close()
		# self._stop('Srvc:'+ self.bind_to)

	def get(self, msg):
		jmsg = json.dumps(msg)
		self.socket.send(jmsg)
		jmsg = self.socket.recv()
		msg = json.loads(jmsg)
		return msg


#############################################################################################
# Tests
# nosetests -v zmqclass.py

# def test_pub_sub():
# 	pub = Pub('tcp://127.0.0.1:9000')
# 	sub = Sub('test', 'tcp://127.0.0.1:9000')
# 	tmsg = {'a': 1, 'b': 2}
# 	while True:
# 		pub.pub('test', tmsg)
# 		topic, msg = sub.recv()
#
# 		if msg:
# 			assert msg == tmsg
# 			break
#
#
# # for some reason, windows barfs on this inside of the test_service() and I have
# # to put it out here!!!!!
# import multiprocessing as mp
# class tServer(mp.Process):
# 	def __init__(self):
# 		mp.Process.__init__(self)
#
# 	def run(self):
# 		serv = ServiceProvider('tcp://127.0.0.1:9000')
# 		serv.listen(self.callback)
# 		return 0
#
# 	def callback(self, msg):
# 		return msg
#
# def test_serivce():
# 	import multiprocessing as mp
# 	# import time
#
# 	ans = {'a': 1, 'b': 2}
#
# 	# class tServer(mp.Process):
# 	# 	def __init__(self):
# 	# 		mp.Process.__init__(self)
# 	#
# 	# 	def run(self):
# 	# 		serv = ServiceProvider('tcp://127.0.0.1:9000')
# 	# 		serv.listen(self.callback)
# 	# 		return 0
# 	#
# 	# 	def callback(self, msg):
# 	# 		return msg
#
# 	s = tServer()
# 	s.start()
#
# 	client = ServiceClient('tcp://127.0.0.1:9000')
# 	msg = client.get(ans)
# 	assert msg == ans
#
# 	s.terminate()
# 	s.join()


if __name__ == "__main__":
	print 'hello cowboy!'
	pass
