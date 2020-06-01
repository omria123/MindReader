import wrapt

from ..manager import driver


@driver('object')
class ObjectDriver(wrapt.ObjectProxy):
	"""
	Driver which let the user send it's own driver in the URL, (Excellent for testing).
	"""

	def __init__(self, wrapped, *args, **kwargs):
		super().__init__(wrapped)
		self._args = args
		self._kwargs = kwargs