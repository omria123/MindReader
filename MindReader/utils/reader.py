import json
import struct

from .protobuf.cortex_pb2 import User, Snapshot

from . import Drivers

DEFAULT_READER = 'json'
DEFAULT_READERS = {'sample': 'protobuf'}

_readers = {}


##########################
# Exported APId
##########################
def read_object(url, *args, scheme=None, read_format=None, obj=None, **kwargs):
	"""
	Read an obj from the given url.
	Optional: Read the file in respect to a given scheme encoded in the url.
	:param url: URL which indicates where should we read from.
	:param obj: Optional - The readers are divides to themes, but there can also be fast accessed fast
	if they have no theme (It's simply nicer to organize, for example have 3 types of sample readers).
	:param read_format: Optional - Customize reader to read from.
	:param scheme: Optional - scheme which chooses driver. Can also be integrated in the URL.
	:param args, kwargs: extra arguments to give to the driver.
	:return: An obj which is read directly by the reader.
	"""
	if scheme is None:
		scheme = Drivers.DEFAULT_SCHEME
		if '://' in url:
			scheme, url = url.split('://', 1)

	driver = Drivers.find_driver(scheme)
	if read_format is None:
		read_format = DEFAULT_READERS[obj]

	return _readers[(obj, read_format)](url, driver, *args, **kwargs)


def sample_reader(version):
	"""
	Second level decorator which collect sample readers.
	The usual case would be add more readers for the sample, so it nicer to have a private case decorator to it.
	(Instead of seeing a lot of ('sample', some_version)
	:param version: the version of the sample reader
	"""

	def decorator(obj):
		return reader(('sample', version))(obj)

	return decorator


def reader(name):
	"""
	Second level decorator which collects readers.
	:param name: the name of the reader, can be any Immutable which later will identify this requested reader.
	"""

	def decorator(obj):
		_readers[name] = obj
		return obj

	return decorator


##########################
# READERS
##########################
@sample_reader('protobuf')
def read_protobuf_sample(url, driver):
	"""
	Reads the Sample, with the injected driver interface
	:param url: URL to give the driver (where to read from)
	:param driver: Injected driver which decides how to access the url
	:return: User, Read
	"""
	# Fixed fields for this format
	fields = [{'pose': ['translation', 'rotation']}, 'color_image', 'depth_image', 'timestamp', 'feeling']

	fd = driver(url, mode='rb')
	messages = read_messages(fd)
	user = User.FromString(next(messages))
	snapshots = map(Snapshot.FromString, messages)

	return user, snapshots


@reader('json')
def read_json(url, driver):
	"""
	Reads the config, using an injected driver interface.
	The driver must also support the json.
	:param url: Where to read from.
	:param driver: Driver to read from.
	:return: The json stored in the fd.
	"""
	with driver(url, 'rb') as fd:
		if hasattr(fd, 'json'):  # If the driver already exports jsons function
			return fd.json()
		return json.load(fd)


@reader(('snapshot_protocol', 'protobuf'))
def read_snapshot_protocol_protobuf(url, driver):
	"""
	Reads snapshot in protobuf format, from the given URL using the driver.
	The file in the URL contains the snapshot only
	:param url: Where to read from.
	:param driver: Driver to use for reading.
	:return: Snapshot obj
	"""
	with driver(url, 'rb') as fd:
		return Snapshot.ParseFromString(fd.read())


@reader(('user', 'json'))
def read_user_json(url, driver):
	"""
	Reads the user obj in json format from the url with the given driver.
	The json should hold the dict which represents the attributes of the user. (i.e. user_id ...)
	:param url: URL to read from.
	:param driver: Driver which should be used for reading
	:return: User obj which should be converted to JSON.
	"""
	return type('User', (object,), read_json(url, driver))


##########################
# Helper functions
##########################
def read_messages(fd, *, close_fd=True):
	"""
	This generator yields the a message after which exists in stream
	A message is in format of (32 bit of unsigned length) | (message_bytes)
	Note: By default this function is responsible to close the fd, since it's being as a co-routine, it may take a while
	(In code terms) until it closes. This can be overridden inserting close_fd=False
	:param fd: A file like obj with read functionality
	:param close_fd: Whether or not to close the file when finished
	:return: iterator of strings
	"""
	while True:
		try:
			length_bin = fd.read(4)
			if len(length_bin) == 0:
				break

			l, = struct.unpack('<L', fd.read(4))
			yield fd.read(l)
		except StopIteration:
			break
	if close_fd:
		fd.close()


'''
#def build_object(attrs, name='new_object'):
	"""
	Build basic obj from dictionary of objects.
	:param attrs: dict of attr, value pairs which describes the obj.
	:param name: The dunder name of the obj.
	"""
	return type(name, (obj,), attrs)
'''
