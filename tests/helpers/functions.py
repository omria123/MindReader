import contextlib
import struct


def add_len_prefix(bytes_string):
	return struct.pack('<L', len(bytes_string)) + bytes_string


@contextlib.contextmanager
def uncloseable(fd):
	"""
	Context manager which turns the fd's close operation to no-op for the duration of the context
	"""
	close = fd.close
	fd.close = lambda: None  # Trick the writer so it won't close it
	yield
	fd.close = close

