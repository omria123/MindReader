from .utils import Connection, read_object


def upload_sample(path, host, port, sample_reader=None):
	"""
	upload from sample at path to server at host:port
	:param path: Path to a sample to upload
	:param host: IP address of the server which should get the sample
	:param port: The port which the server listens to.
	:param sample_reader: Optional - The caller has the full freedom to choose specific sample reader, from the
	reader module.
	"""
	user, snapshots = read_object(path, object=sample_reader)
	conn = Connection(f'http://{host}:{port}', user)
	publish_sample(snapshots, conn.upload)


def publish_sample(snapshots, publish):
	"""
	:param snapshots: Iterable of the snapshots from the sample
	:param publish: Injected function to publish a snapshot
	"""
	for snapshot in snapshots:
		publish(snapshot)
