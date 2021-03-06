"""
Test client to db communication
"""
import io
import itertools
import os
import signal
import time
from multiprocessing import Process

from google.protobuf.json_format import MessageToDict

from MindReader import IOAccess
from MindReader.client import upload_sample


def test_client_db(cli_server, db, mq, sample_factory, all_workers):
	amount = 11
	user, snapshots = sample_factory(amount)
	sample_snapshots, compare_snapshots = itertools.tee(snapshots)
	open_pids = []
	sample_snapshots = list(sample_snapshots)
	compare_snapshots = list(compare_snapshots)

	# Client prep
	def run_client():
		time.sleep(1.5)  # Wait for everyone to start
		with io.BytesIO() as sample_file:
			IOAccess.write(sample_file, 'sample', user, sample_snapshots)
			sample_file.seek(0)
			upload_sample(sample_file, cli_server.host, cli_server.port, scheme='object')
		time.sleep(7)
		for pid in open_pids:
			os.kill(pid, signal.SIGINT)

	# Start workers
	workers_proc = Process(target=all_workers, args=(mq.url, db.url))
	workers_proc.start()
	open_pids.append(workers_proc.pid)
	# Start server
	server_proc = Process(target=cli_server, args=(mq.url,))
	server_proc.start()
	open_pids.append(server_proc.pid)

	# Start client
	open_pids.append(os.getpid())
	Process(target=run_client).start()

	try:
		while 1:
			time.sleep(1)
	except KeyboardInterrupt:
		pass

	# Testing
	db_handler = db()
	db_user = db_handler.get_user(user.user_id)
	db_snapshots = db_handler.get_snapshots(str(user.user_id))

	assert MessageToDict(user, preserving_proto_field_name=True, including_default_value_fields=True,
	                     use_integers_for_enums=True) == db_user
	counter = 0
	for compare_snapshot in compare_snapshots:
		counter += 1
		success = False
		for db_snapshot in db_snapshots:
			assert db_snapshot['user_id'] == str(user.user_id)
			if db_snapshot['timestamp'] != compare_snapshot.datetime:
				continue
			success = True
		assert success

	assert amount == counter  # No extras
