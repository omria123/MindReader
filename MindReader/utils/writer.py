import json
import struct

from . import Drivers

from .cortex_pb2 import User, Snapshot
from .cortex_pb2 import Snapshot as SnapshotNet  # The protocol might change and the client-server encoding should

# be different from the reader Snapshot

DEFAUlLT_WRITER = 'json'

DEFAULT_WRITERS = {'sample': 'protobuf', 'user': 'json', 'snapshot_protocol': 'protobuf'}

USER_FIELDS = ['username', 'user_id', 'birthday', 'gender']

_writers = {}


##########################
# Exported API
##########################
def write_object(url, *args, scheme=None, write_format=None, object=None, **kwargs):
	"""
	Writes an object from the given url.
	Optional: Writes the file in respect to a given scheme encoded in the url.
	:param url: URL which we should write to.
	:param args, kwargs: Data to pass to the specific writer
	:param scheme: Optional - scheme which chooses driver. Can also be integrated in the URL.
	:param object: Optional - The writers are divides to themes, but there can also be fast accessed fast
	if they have no theme (It's simply nicer to organize, for example have 3 types of sample writers).
	:param write_format: Optional - Customize writer to writer from.
	:return: An object which is writer directly by the writer.
	"""
	if scheme is not None:
		scheme = Drivers.DEFAULT_SCHEME
		if '://' in url:
			scheme, url = url.split('://', 1)

	driver = Drivers.find_driver(scheme)
	if write_format is None:
		write_format = DEFAULT_WRITERS[object]

	return _writers[(object, write_format)](url, driver, *args, **kwargs)


def sample_writer(version):
	"""
	Second level decorator which collect sample writers.
	The usual case would be add more writers for the sample, so it nicer to have a private case decorator to it.
	(Instead of seeing a lot of ('sample', some_version)
	:param version: the version of the sample writer
	"""

	def decorator(obj):
		return writer(('sample', version))(obj)

	return decorator


def writer(name):
	"""
	Second level decorator which collects writers.
	:param name: the name of the writer, can be any Immutable which later will identify this requested _writer.
	"""

	def decorator(obj):
		_writers[name] = obj
		return obj

	return decorator


##########################
# WRITERS
##########################
@writer('json')
def write_json(url, driver, data):
	"""
	Writes the config, using an injected driver interface.
	The driver must also support the json.
	:param url: Where to write to.
	:param driver: Driver which should be used for writing.
	:param data: What should be written
	:return: The response of the Driver's fd. (I have made it possible for writer driver to return some value)
	"""
	fd = driver(url, 'wb')
	if hasattr(data, 'json'):
		fd.write(data.json())  # If the object has inner implementation
	else:
		json.dump(data, fd)
	return fd.close()


@writer('post')
def write_post(url, driver, body, *, headers=None):
	"""
	Write POST request to some driver.
	If the driver can handle write of headers, it would be written in the driver implemented function.
	Otherwise, the typical string conversion would be the default case for no inner implementation.
	:param url: URL to write to.
	:param driver:  Driver which should be used for writing.
	:param body: Body of the POST request
	:param headers: Optional - Headers of the POST request
	:return:
	"""
	mode = 'wb' if type(body) is bytes else 'w'

	with driver(url, mode) as fd:
		generic_write_headers(fd, headers)
		fd.write(body)


@writer(('user', 'json'))
def write_user_json(url, driver, user):
	"""
	Write the user object in json format to the url with the given driver.
	:param url: URL to write to.
	:param driver: Driver which should be used for writing
	:param user: User object which should be converted to JSON.
	"""
	# Naive attempt:
	try:
		return write_json(url, driver, user)
	except TypeError:
		pass
	# Manual Converting:
	user_dict = {}
	for field in USER_FIELDS:
		if hasattr(user, field):
			user_dict[field] = user.field
	return write_json(url, driver, user_dict)


@writer(('snapshot_protocol', 'protobuf'))
def write_snapshot_protocol_protobuf(url, driver, snapshot, fields, *, headers=None):
	"""
	Writes the snapshot to the file according to the protocol of the client-server communication.

	:param url: The URL which the snapshot is written to.
	:param driver: The driver used to access the URL for writing.
	:param snapshot: Snapshot object which should be written.
	:param fields: Filtering on the snapshot object's fields.
	:param headers: Optional - For HTTP support, we add insertion of headers.
	:return: The response of the writing for supporting drivers which return values in the close. (Like the HTTP driver)
	"""
	ess_snapshot = SnapshotNet()
	fd = driver(url, 'wb')
	for field in fields:
		if hasattr(snapshot, field):
			setattr(ess_snapshot, field, getattr(snapshot, field))
	generic_write_headers(fd, headers)
	fd.write(ess_snapshot.SerializeToString())
	return fd.close()


@sample_writer('protobuf')
def write_protobuf_sample(url, driver, sample):
	"""
	Writes the Sample, with the injected driver interface
	:param sample: Sample object which should be written.
	:param url: URL to give the driver (where to write to)
	:param driver: Injected driver which decides how to access the url
	:return:
	"""
	with driver(url, 'wb') as fd:
		fd.write(sample.user.SerializeToString())
		for snapshot in sample.snapshots:
			fd.write(snapshot)


##########################
# Helper functions
##########################
def write_messages(fd, strings, *, close_fd=True):
	"""
	This generator turn each string in the strings iterable into a message and yields the result.
	A message is in format of (32 bit of unsigned length) | (message_bytes)
	Note: By default this function is responsible to close the fd, since it's being as a co-routine, it may take a while
	(In code terms) until it closes. This can be overridden inserting close_fd=False
	:param fd: A file like object with write functionality
	:param strings: An iterable of strings which should be transformed
	:param close_fd: Whether or not to close the file when finished
	:return: iterator of messages
	"""

	for string in strings:
		if type(string) is str:
			string = string.encode()
		fd.write(struct.pack('<L', len(string) + string))

	if close_fd:
		fd.close()


def generic_write_headers(fd, headers, mode='wb'):
	"""
	Writes headers if they exists (not None) to the file, according to wb.
	If the file descriptor's driver supports `write_headers` functionality, it would be used.
	Otherwise the function will write the headers as the native str of the object headers.
	:param fd: Some file-like object opened in write mode.
	:param headers: headers which should be written
	:param mode: The mode of writing
	"""
	if headers is not None:
		if hasattr(fd, 'write_headers'):
			fd.write_headers(headers)
		else:
			headers_string = str(headers)
			if 'b' in mode:
				headers_string = headers.encode()
			fd.write(headers_string)
