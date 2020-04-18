class ObjectFile:
	"""
	In case some special case obj is needed, this driver wraps the obj (which is simply the given URL)
	The driver simply wraps the obj completely.
	Note that obj must serve as a fully qualified file interface
	"""

	def __init__(self, obj, *args, **kwargs):
		self._wrapped_obj = obj
		for attr in obj.__dict__:
			if not attr.startswith('_'):
				setattr(self, attr, getattr(obj, attr))

	def __enter__(self):
		return self._wrapped_obj

	def __exit__(self, exc_type, exc_val, exc_tb):
		pass

	def close(self):
		return self._wrapped_obj
