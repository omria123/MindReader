from .utils import Config, Connection, Session, Reader


def upload_sample(host, port, path):
	"""
	upload from sample at path to server at host:port
	:param host: ip of server
	:param port: port of server
	:param path: path to sample
	"""
	reader = Reader(path)
	config = Config(reader.fields)

	with Session.client(Connection((host, port)), config) as session:
		session.send_user(reader.user)
		for snapshot in reader.snapshots:
			session.send_snapshot(snapshot)
