import io
import itertools
import struct

from MindReader.client import publish_sample

USER = None


def test_publish_sample(sample_factory):
	"""
	Checks that the  client tries to publish the actual thing it should upload.
	This doesn't check the client use of the connection object.
	I simply check separately the Connection class and if it's good than all is good.
	"""
	user, snapshots = sample_factory()
	data = string_to_message(user.SerializeToString())
	sample_snapshots, compare_snapshots = itertools.tee(snapshots)

	def publish_user(new_user):
		assert user == new_user

		def publish_snapshot(snapshot):
			assert snapshot == next(compare_snapshots)

		return publish_snapshot

	for snapshot in sample_snapshots:
		data += string_to_message(snapshot.SerializeToString())

	with io.BytesIO() as fd:
		fd.write(data)
		publish_sample(fd, publish_user=publish_user, scheme='object')


def string_to_message(st):
	return struct.pack('<L', len(st)) + st
