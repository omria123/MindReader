import itertools
import time

from google.protobuf.json_format import MessageToDict

import MindReader
import MindReader.utils


def test_pipeline(sample_factory, tmp_path, server, mq, db):
	user, snapshots = sample_factory()
	sample_snapshots, compare_snapshots = itertools.tee(snapshots)
	sample_path = str(tmp_path / 'sample')
	with open(str(tmp_path / 'sample'), 'wb') as fd:
		MindReader.IOAccess.write(fd, 'sample', user, sample_snapshots)

	MindReader.upload_sample(sample_path, server.host, server.port)
	time.sleep(10)  # Giving extra time for the pipeline to work

	assert [(user.username, user.user_id)] == db.get_users()
	assert MessageToDict(user) == db.get_user(user)
	assert set([(snapshot.datetime, snapshot.DESCRIPTOR.fields_by_name.keys()) for snapshot in
	            compare_snapshots]) == set(db.get_snapshots(user.user_id))
