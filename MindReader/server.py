import contextlib

from .utils import Listener

DEBUG_FLAG = False

PARSABLE_FIELDS = []  # TODO: change
BIG_DATA_FIELDS = []  # TODO: change


# DONT USE
def add_debug(prn):
	"""
	Add a debug functionality to the publish function
	The debug will work only if it allowed by prn function and
	by global constant DEBUG_FLAG
	:param prn: the publish function for run_server
	:return: the new publish function
	"""

	@contextlib.contextmanager(prn)
	def wrapper(snapshot):
		if DEBUG_FLAG and (not hasattr(prn, 'DEBUG') or prn.DEBUG):
			prn(repr(snapshot))
		else:
			prn(snapshot)

	return wrapper


def run_server(host, port, publish=print):
	"""
	run server bind to host:port, read snapshots from
	connections and publish by given function
	:param host: ip for binding
	:param port: port for binding
	:param publish: what to do with given snapshots
	"""
	# publish = add_debug(publish)

	server = Listener((host, port), publish)
	server.run_forever()
