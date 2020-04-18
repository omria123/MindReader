from gzip import open as gzip_open

from .object_file import ObjectFile

_drivers = {'file': open, 'gzip': gzip_open, 'obj': ObjectFile}
DEFAULT_SCHEME = 'file'


def find_driver(scheme):
	return _drivers[scheme]


def driver(name):
	"""
	Second order decorator for class/function to collect drivers for the _drivers dict.
	:param name: The name of the resource that the driver is implementing
	:return: First order decorator
	"""

	def decorator(obj):
		"""
		Collects the function/class to the name described in outer scope to _drivers
		:param obj: function/class which implements the driver functionality
		"""
		_drivers[name] = obj
		return obj

	return decorator
