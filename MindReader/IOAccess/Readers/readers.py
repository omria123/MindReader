import io
import json
import struct

from google.protobuf.json_format import MessageToDict

from ..manager import reader
from MindReader.utils.protobuf import Snapshot, User


@reader('sample')
@reader('sample', 'protobuf', 'application/protobuf')
def read_protobuf_sample(fd):
	"""
	Reads the Sample, with the injected Driver interface
	"""
	messages = read_messages(fd)
	with io.BytesIO(next(messages)) as fd:
		user = read_user_protobuf(fd)
	snapshots = map(Snapshot.FromString, messages)
	return user, snapshots


@reader('user')
@reader('user', 'protobuf', 'application/protobuf')
def read_user_protobuf(fd):
	return MessageToDict(User.FromString(fd.read()), preserving_proto_field_name=True,
	                     including_default_value_fields=True, use_integers_for_enums=True)


@reader('snapshot')
@reader('snapshot', 'protocol_protobuf', 'application/protobuf')
@reader('snapshot', 'protobuf')  # They are the same for now
def read_snapshot_protobuf(fd):
	return Snapshot.FromString(fd.read())


@reader('json')
@reader('user', 'json', 'application/json')
def read_json(fd):
	"""
	Reads json from generic fd.
	"""
	if hasattr(fd, 'json'):  # If the Driver already exports jsons function
		return fd.json()
	return json.load(fd)


##########################
# HELPER FUNCTIONS
##########################
def read_messages(fd, *, force_open=True):
	"""
	Read messages of the format (len | string)
	"""
	close = None
	if force_open:
		close = fd.close
		fd.close = lambda: None
	while True:
		raw_len = fd.read(4)
		if len(raw_len) == 0:
			break
		l, = struct.unpack('<L', raw_len)
		yield fd.read(l)
	if force_open:
		fd.close = close
	close()
