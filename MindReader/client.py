from .utils import Connection, read_object

DEFAULT_SCHEME = 'gzip'


def upload_sample(path, host, port, *, sample_reader=None, scheme=None):
	"""
	upload from sample at path to server at host:port
	:param path: Path to a sample to upload
	:param host: IP address of the server which should get the sample
	:param port: The port which the server listens to.
	:param sample_reader: Optional - The caller has the full freedom to choose specific sample reader, from the
	reader module.
	:param scheme: Optional - The caller can decide on some scheme according to the request of the client.
	The scheme can also be encoded to the URL, in such case scheme should be None.
	"""
	if scheme is None:
		scheme = DEFAULT_SCHEME
	user, snapshots = read_object(path, obj=sample_reader, scheme=scheme)
	conn = Connection(f'http://{host}:{port}', user)
	publish_sample(snapshots, conn.upload)


def publish_sample(snapshots, publish):
	"""
	:param snapshots: Iterable of the snapshots from the sample
	:param publish: Injected function to publish a snapshot
	"""
	for snapshot in snapshots:
		publish(snapshot)
