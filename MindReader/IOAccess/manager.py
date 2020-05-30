import gzip

from MindReader.defaults import DEFAULT_SCHEME

DRIVERS = {'file': open, 'gzip': gzip.open}
WRITERS = {'_general': {}}
READERS = {'_general': {}}
WRITERS_MIME_TYPE = {}
READERS_MIME_TYPE = {}

CONTEXT = {
	'read': {
		'mime_dict': READERS_MIME_TYPE,
		'functions_dict': READERS,
		'not_found': 'No such reader is available',
	},
	'write': {
		'mime_dict': WRITERS_MIME_TYPE,
		'functions_dict': WRITERS,
		'not_found': 'No such writer is available',
	}}


###########################
# MODULE INFO FUNCTIONS
###########################

def object_access(operation, name, specify_func):
	accessors = CONTEXT[operation]['functions_dict'][name]
	return accessors.items() if specify_func else accessors.keys()


def object_writers(name, *, specify_writer=False):
	"""
	For given object name, gives all the possible formats which it can be written in.
	:return: iterable of the available formats.
	Optional - if specify_writer is true return the actual writer with it. (As pairs)
	"""

	return object_access('write', name, specify_writer)


def object_readers(name, *, specify_reader=False):
	"""
	For given object name, gives all the possible formats which it can be read.
	:return: iterable of the available formats.
	Optional - if specify_reader is true return the actual reader with it. (As pairs)
	"""
	return object_access('read', name, specify_reader)


###############################
# COLLECTORS
###############################

def reader(name, version=None, mimetype=None):
	"""
	Second level decorator which collects readers.
	:param name: Short description of the object being read. Will be used for accessing the reader.
	:param version: Optional - Specify a version for this specific reader.
	:param mimetype: Add a mimetype description for the reader.
	"""
	return _data_processor('read', name, version, mimetype)


def writer(name, version=None, mimetype=None):
	"""
	Second level decorator which collects writers.
	:param name: Short description of the object being written. Will be used for accessing the writer.
	:param version: Optional - Specify a version for this specific writer.
	:param mimetype: Add a mimetype description for the writer.
	"""
	return _data_processor('write', name, version, mimetype)


def _data_processor(operation, name, version=None, mimetype=None):
	context = CONTEXT[operation]

	def decorator(obj):
		if version is None:
			context['functions_dict']['_general'][name] = obj
			return obj

		if mimetype is not None:
			if name not in context['mime_dict']:
				context['mime_dict'][name] = {}
			context['mime_dict'][name][mimetype] = version

		if name not in WRITERS:
			context['functions_dict'][name] = {}

		context['functions_dict'][name][version] = obj

		return obj

	return decorator


###########################
# IO ACCESS FUNCTIONS
###########################

def open(url, *args, **kwargs):
	"""
	This is a simple use for any driver.
	The url may encode the scheme to choose the driver, otherwise it will use the default one.
	:param url: The URL/Path which is used to give to the Driver.
	"""
	scheme = DEFAULT_SCHEME
	if '://' in url:
		scheme, url = url.split('://')
	return DRIVERS[scheme](url, *args, **kwargs)


def driver(name):
	"""
	Second order decorator for class/function to collect drivers for the DRIVERS dict.
	:param name: The name of the resource that the Driver is implementing
	:return: First order decorator
	"""

	def decorator(obj):
		"""
		Collects the function/class to the name described in outer scope to DRIVERS
		:param obj: function/class which implements the Driver functionality
		"""
		DRIVERS[name] = obj
		return obj

	return decorator


def access(operation, fd, name, *args, version=None, **kwargs):
	context = CONTEXT[operation]
	if version is None:  # General reader, with no versions division.
		name, version = '_general', name
	try:
		selected = context['functions_dict'][name][version]
	except KeyError:
		raise ValueError(context['not_found'])

	return selected(fd, *args, **kwargs)


def read(fd, name, *args, version=None, **kwargs):
	"""
	Selecting a reader to read from an given fd.
	"""
	return access('read', fd, name, *args, version=version, **kwargs)


def write(fd, name, *args, version=None, **kwargs):
	"""
	selecting a writer to read from given fd
	"""
	return access('write', fd, name, *args, version=version, **kwargs)


def read_url(path, name, *args, version=None, driver_kwargs=None, scheme=None, **kwargs):
	"""
	Faster access to write to some url.
	"""
	if driver_kwargs is None:
		driver_kwargs = {}
	fd = open(path, **driver_kwargs) if scheme is None else DRIVERS[scheme](path, **driver_kwargs)
	data = read(fd, name, *args, version=version, **kwargs)
	fd.close()
	return data


def write_url(path, name, *args, version=None, driver_kwargs=None, scheme=None, **kwargs):
	"""
	Faster access to write to some url.
	"""
	if driver_kwargs is None:
		driver_kwargs = {}
	fd = open(path, **driver_kwargs) if scheme is None else DRIVERS[scheme](path, **driver_kwargs)
	write(fd, name, *args, version=version, **kwargs)
	return fd.close()
