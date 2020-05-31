"""
Tests the pipeline from the client to the server
"""
import io
import itertools
import json
import os
import signal
import time
from multiprocessing import Process

from google.protobuf.json_format import MessageToDict

from MindReader import IOAccess
from MindReader.client import upload_sample


def test_client_queue(mq, cli_server, sample_factory):
	amount = 10
	user, snapshots = sample_factory(10)
	sample_snapshots, compare_snapshots = itertools.tee(snapshots)
	compare_snapshots = set(snapshot.SerializeToString() for snapshot in compare_snapshots)
	published_snapshots = set()
	published_user = None

	# MQ Preparation
	def fake_parser_callback(channel, delivery, properties, body):
		with open(body, 'rb') as fd:
			data = fd.read()
		assert data in compare_snapshots
		published_snapshots.add(data)

	def saver_callback(channel, delivery, properties, body):
		nonlocal published_user
		published_user = json.loads(body)

	mq_handler = mq()
	mq_handler.channel.queue_declare(queue='saver', durable=True)
	mq_handler.channel.basic_consume(queue='saver', on_message_callback=saver_callback)

	mq_handler.channel.exchange_declare(exchange='raw_snapshot', exchange_type='fanout')
	mq_handler.channel.queue_declare(queue='testing_queue', durable=True)
	mq_handler.channel.queue_bind(queue='testing_queue', exchange='raw_snapshot')
	mq_handler.channel.basic_consume(queue='testing_queue',
	                                 on_message_callback=fake_parser_callback)  # TODO: check auto_ack

	# Client preparation:
	def run_client():
		time.sleep(1.5)  # Wait for everyone to start
		with io.BytesIO() as sample_file:
			IOAccess.write(sample_file, 'sample', user, sample_snapshots)
			sample_file.seek(0)
			upload_sample(sample_file, cli_server.host, cli_server.port, scheme='object')
		time.sleep(15)  # Wait for everyone to finish
		os.kill(server_pid, signal.SIGINT)
		os.kill(os.getppid(), signal.SIGINT)

	# Server start
	server_proc = Process(target=cli_server, args=(mq.url,))
	server_proc.start()
	server_pid = server_proc.pid

	# Client invocation
	Process(target=run_client, args=()).start()

	# MQ start
	try:
		mq_handler.channel.start_consuming()
	except KeyboardInterrupt:
		pass

	# Actual testing
	assert MessageToDict(user, preserving_proto_field_name=True, including_default_value_fields=True,
	                     use_integers_for_enums=True) == published_user
	assert len(published_snapshots) == amount
	assert published_snapshots == compare_snapshots

	# Teardown

	mq_handler.close()
