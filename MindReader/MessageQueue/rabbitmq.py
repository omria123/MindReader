import json
import logging
import functools
from pathlib import Path

import pika

from .. import IOAccess

logger = logging.getLogger('MessageQueue')


def body_json(f):
	@functools.wraps(f)
	def wrapper(channel, method, properties, body):
		if isinstance(body, bytes):
			body = body.decode()
		return f(channel, method, properties, json.loads(body))

	return wrapper


def publish_json(f):
	@functools.wraps(f)
	def wrapper(self, message, channel=None):
		return f(self, json.dumps(message), channel)

	return wrapper


class RabbitMQ:
	scheme = 'rabbitmq'
	DEFAULT_PORT = 5672

	def __init__(self, host, port=None):
		if port is None:
			port = self.DEFAULT_PORT
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, int(port)))
		self.channel = self.connection.channel()

		logger.info('Message Queue connected')
		logger.debug(f'The message queue is at {host}:{port}')

	@publish_json
	def publish_user(self, user, channel=None):
		if channel is None:
			channel = self.channel
		logger.debug('Uploading user to saver queue')
		channel.queue_declare(queue='saver', durable=True)
		channel.basic_publish(exchange='', routing_key='saver', body=user,
		                      properties=pika.BasicProperties(delivery_mode=2))
		logger.debug('New user on saver queue')

	def publish_snapshot(self, snapshot, channel=None):
		if channel is None:
			channel = self.channel
		logger.debug('Publishing new snapshot...')
		channel.exchange_declare(exchange='raw_snapshot', exchange_type='fanout')
		channel.basic_publish(exchange='raw_snapshot', body=snapshot, routing_key='',
		                      properties=pika.BasicProperties(delivery_mode=2))
		logger.debug('new snapshot published')

	@publish_json
	def publish_result(self, result, channel=None):
		if channel is None:
			channel = self.channel
		logger.debug('Publishing new result...')
		channel.queue_declare(queue='saver', durable=True)
		channel.basic_publish(routing_key='saver', exchange='', body=result,
		                      properties=pika.BasicProperties(delivery_mode=2))
		logger.debug(f'New result published {result}')

	def run_parser(self, name, parser, start_consuming=True):
		"""
		Running parser which feeds on the message queue.
		Passing the parser every field it needs from the snapshot, and publishes the result.
		"""

		def callback(channel, method, properties, body):
			logger.info('New raw snapshot received')
			raw_snapshot_path = Path(body.decode())
			user_id = str(raw_snapshot_path.parent.parent.name)
			snapshot_id = str(raw_snapshot_path.parent.name)

			db_result = parser(raw_snapshot_path)
			if db_result is None:  # Nothing to publish
				channel.basic_ack(delivery_tag=method.delivery_tag)
				return

			db_result.update({'snapshot_id': snapshot_id, 'user_id': user_id})
			self.publish_result(db_result, channel=channel)

			channel.basic_ack(delivery_tag=method.delivery_tag)

		self.channel.exchange_declare(exchange='raw_snapshot', exchange_type='fanout')
		self.channel.queue_declare(queue=name, durable=True)
		self.channel.queue_bind(queue=name, exchange='raw_snapshot')
		self.channel.basic_consume(queue=name, on_message_callback=callback)

		if start_consuming:
			self.consume()

	def run_saver(self, saver, start_consuming=True):
		"""
		Assigns a saver to the Message Queue.
		"""

		@body_json
		def callback(channel, method, properties, body):
			logger.info('Got new message to save')
			logger.debug(body)
			if 'gender' and 'birthday' in body:  # Save user
				logger.info('Saving user...')
				saver.save_user(body)
			else:
				logger.info('Saving snapshot....')
				name = body
				saver.save(name, body)
			channel.basic_ack(delivery_tag=method.delivery_tag)

		logger.info('New Saver is assigned')

		self.channel.queue_declare(queue='saver', durable=True)
		self.channel.basic_consume(queue='saver', on_message_callback=callback, auto_ack=False)
		if start_consuming:
			self.consume()

	def consume(self):
		logger.info('Starts consuming...')
		self.channel.start_consuming()

	def close(self):
		self.connection.close()
