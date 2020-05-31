import io
import json
import struct

from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import Message

from MindReader.utils.protobuf.cortex_pb2 import User, Snapshot
from MindReader.utils.protobuf import object_to_protobuf
from ..manager import writer


##########################
# WRITERS
##########################
@writer('json')
def write_json(fd, data, mode='w'):
	if hasattr(data, 'json'):  # If the obj has inner implementation
		result = data.json()
	else:
		result = json.dumps(data)
	if 'b' in mode:
		result = result.encode()
	fd.write(result)


@writer('post')
def write_post(fd, body, *, headers=None):
	"""
	Write POST request to some Driver.
	"""
	generic_write_headers(fd, headers)
	fd.write(body)


@writer('user', 'json', 'application/json')
def write_user_json(fd, user, mode='w'):
	# Naive attempt:
	try:
		return write_json(fd, user, mode)
	except TypeError:
		pass

	if isinstance(user, Message):
		d = MessageToDict(user, including_default_value_fields=True, preserving_proto_field_name=True,
		                  use_integers_for_enums=True)
		return json.dump(d, fd)  # Even naiver attempt

	user_dict = {}
	for field in User.DESCRIPTOR.fields_by_name:  # Use the descriptor to find out User's fields
		if hasattr(user, field):
			user_dict[field] = getattr(user, field)
	return write_json(fd, user_dict, mode)


@writer('user')
@writer('user', 'protobuf')
def write_user_protobuf(fd, user):
	if isinstance(user, User):  # The easy way out
		return fd.write(user.SerializeToString())

	if isinstance(user, dict):
		new_user = User()
		ParseDict(user, new_user, ignore_unknown_fields=True)
		return write_user_protobuf(fd, user)
	# Mostly won't happen but support it nevertheless
	new_user = User()
	for field in User.DESCRIPTOR.fields_by_name:
		if hasattr(user, field):
			setattr(new_user, user, getattr(user, field))

	return fd.write(new_user.SerializeToString())


@writer('snapshot')
@writer('snapshot', 'protobuf')
@writer('snapshot', 'protocol_protobuf', 'application/protobuf')
def write_snapshot_protobuf(fd, snapshot, fields=None):
	if isinstance(snapshot, Snapshot):  # The easy way out
		return fd.write(snapshot.SerializeToString())

	new_snapshot = snapshot
	if not isinstance(snapshot, Snapshot):
		new_snapshot = Snapshot()
		object_to_protobuf(snapshot, new_snapshot)

	for field in new_snapshot.DESCRIPTOR.fields_by_name:
		if fields is not None and field not in fields:
			new_snapshot.ClearField(field)
	return fd.write(new_snapshot.SerializeToString())


@writer('sample')
@writer('sample', 'protobuf', 'application/protobuf')
def write_protobuf_sample(fd, user, snapshots):
	messages = []
	with io.BytesIO() as user_fd:
		write_user_protobuf(user_fd, user)
		messages.append(user_fd.getvalue())

	for snapshot in snapshots:
		with io.BytesIO() as snapshot_fd:
			write_snapshot_protobuf(snapshot_fd, snapshot)
			messages.append(snapshot_fd.getvalue())

	write_messages(fd, messages)


@writer('messages')
def write_messages(fd, strings, *, close_fd=False):
	"""
	Write iterable of strings as messages (len | string) to fd
	"""

	for string in strings:
		if type(string) is str:
			string = string.encode()
		fd.write(struct.pack('<L', len(string)) + string)
	if close_fd:
		fd.close()


##########################
# Helper functions
##########################


def generic_write_headers(fd, headers, mode='wb'):
	"""
	Write HTTP headers to fd. If fd support write_headers, it will use it.
	"""
	if headers is None:
		return

	if hasattr(fd, 'write_headers'):
		fd.write_headers(headers)
		return
	headers_string = '\r\n'.join([f'{str(key)}: {str(value)}' for key, value in headers.items()])
	headers_string += '\r\n\r\n'
	if 'b' in mode:
		headers_string = headers.encode()
	fd.write(headers_string)
