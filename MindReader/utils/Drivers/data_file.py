from io import BytesIO, StringIO

from . import driver


@driver('data')
class DataFile:
	"""
	Fake file easy for testing and a simple example for the whole thing
	The path of the file is it's content in read operation.
	In write mode you can write how much you want, and examine the file contents with
	"""
	DATA_INITIALIZE = {'r': lambda path: StringIO(path), 'rb': lambda path: BytesIO(path.encode),
	                   'w': lambda path: path, 'wb': lambda path: path.encode}

	def __init__(self, path, mode='r'):
		self.mode = mode
		if mode not in self.DATA_INITIALIZE:
			raise TypeError(f'Invalid mode for {self.__class__.__name__}')
		self.data = self.DATA_INITIALIZE[mode](path)

	def read(self, *args):
		if self.mode[0] == 'r':
			return self.data.read(*args)
		else:
			return self.data

	def write(self, data):
		self.data.write(data)

	def close(self):
		return self.data

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		pass
