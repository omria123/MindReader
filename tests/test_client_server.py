"""
Testing the transfer of sample from a user to server
"""
import io
import itertools
import json
import time
from threading import Thread
import signal
import os

from google.protobuf.json_format import MessageToDict

from MindReader import IOAccess
from MindReader.client import upload_sample


def test_client_server(server, sample_factory):
	user, snapshots = sample_factory()
	sample_snapshots, compare_snapshots = itertools.tee(snapshots)
	published_snapshots = []
	published_user = None

	def server_publish_user(new_user):
		nonlocal published_user
		published_user = json.loads(new_user['data'])

	def server_publish_snapshot(user_id, published):
		new_snapshot = published['data']
		published_snapshots.append(new_snapshot)

	def run_client():
		time.sleep(2)
		with io.BytesIO() as sample_file:
			IOAccess.write(sample_file, 'sample', user, sample_snapshots)
			sample_file.seek(0)
			upload_sample(sample_file, server.host, server.port, scheme='object')
		time.sleep(1)
		os.kill(os.getpid(), signal.SIGINT)

	Thread(target=run_client).start()
	server(server_publish_user, server_publish_snapshot)
	time.sleep(5)
	assert published_user == MessageToDict(user, preserving_proto_field_name=True, including_default_value_fields=True,
	                                       use_integers_for_enums=True)
	for snapshot1, snapshot2 in zip(compare_snapshots, published_snapshots):
		assert snapshot1.SerializeToString() == snapshot2
