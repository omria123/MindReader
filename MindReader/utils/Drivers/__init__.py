from io import BytesIO, StringIO
from gzip import open as gzip_open

from . import http_driver
from .data_file import DataFile
from .object_file import ObjectFile

"""
The Drivers is an abstraction an resource, each driver export the same functionality of a file.
The package holds different  
"""

DEFAULT_SCHEME = 'file'

_drivers = {'file': open, 'gzip': gzip_open, 'fake': DataFile}
_drivers.update({'object': ObjectFile})


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
