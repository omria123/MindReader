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
		f(channel, method, properties, json.loads(body))

	return wrapper


def publish_json(f):
	@functools.wraps(f)
	def wrapper(self, message, channel=None):
		return f(self, json.dumps(message), channel)

	return wrapper


def send_ack(f):
	@functools.wraps(f)
	def wrapper(channel, delivery, properties, body):
		try:
			wrapper(channel, delivery, properties, body)
			channel.basic_ack(delivery_tag=delivery.delivery_tag)
		except Exception as e:
			logger.error(e)


class RabbitMQ:
	scheme = 'rabbitmq'
	DEFAULT_CONFIG = {'raw_user': ['user_parser'], "raw_snapshot": ['snapshot_parser']}
	DEFAULT_EXCHANGE_TYPE = 'fanout'
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
		logger.debug('New result published')

	def run_parser(self, parser, start_consuming=True):
		"""
		Running parser which feeds on the message queue.
		Passing the parser every field it needs from the snapshot, and publishes the result.
		"""
		logger.info(f'New parser of {parser.name} is assigned')
		name = parser.name
		fields = parser.fields

		@send_ack
		def callback(channel, method, properties, body):
			raw_snapshot_path = Path(body)

			user_id = str(raw_snapshot_path.parent.parent)
			snapshot_id = str(raw_snapshot_path.parent)

			logger.info(f'Parser {name} got new work')
			logger.debug(f'The requested snapshot is at: {raw_snapshot_path}')

			snapshot = IOAccess.read_url(str(raw_snapshot_path), 'snapshot', version=raw_snapshot_path.suffix)
			output_path = str(raw_snapshot_path.parent / f'{name}.binary')
			try:
				args = {field: getattr(snapshot, field) for field in fields if field != 'output'}
			except AttributeError:
				logger.info("The snapshot doesn't have the value")
				return
			if 'output' in fields:
				logger.debug(f'The result data will be saved to {output_path}')
				args['output'] = IOAccess.open(output_path, 'wb')

			result = parser(**args)

			logger.info('Parser finished')
			logger.debug(f'Parser returned {result["result"]}')

			if 'output' in args:
				args['output'].close()

			db_result = {
				'result': {name: {'metadata': result}},
				'datetime': snapshot.datetime,
				'snapshot_id': snapshot_id,
				'user_id': user_id
			}
			if 'output' in args:
				db_result['result'][name]['location'] = output_path

			self.publish_result(db_result, channel=channel)

		self.channel.exchange_declare(exchange='raw_snapshot', exchange_type='fanout')
		self.channel.queue_declare(queue=parser.name, durable=True)
		self.channel.bind_queue(queue=parser.name, exchange='raw_snapshot')
		self.channel.basic_consume(queue=parser.name, on_message_callback=callback,
		                           auto_ack=False)  # TODO: check auto_ack
		if start_consuming:
			self.consume()

	def run_saver(self, saver, start_consuming=True):
		"""
		Assigns a saver to the Message Queue.
		"""
		logger.info('New Saver is assigned')

		@body_json
		@send_ack
		def callback(channel, method, properties, body):
			if 'gender' and 'birthday' in body:  # Save user
				logger.info('Saving user...')
				saver.save_user(body)
				return
			logger.info('Saving snapshot....')
			name = body['result'][0]
			saver.save(name, body)

		self.channel.queue_declare(queue='saver', durable=True)
		self.channel.basic_consume(queue='saver', on_message_callback=callback)
		if start_consuming:
			self.consume()

	def consume(self):
		logger.info('Starts consuming...')
		self.channel.start_consuming()

	def close(self):
		self.connection.close()
