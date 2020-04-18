import pika

PARSABLE_FIELDS = []  # TODO: change!!!!
MQ_MANAGERS = {}


def resolve_mq_manager(scheme):
	"""
	Finds the appropriate message queue manager for the given scheme.
	:param scheme: A URL's scheme like rabbitmq
	"""
	return MQ_MANAGERS[scheme]


def message_queue(cls):
	"""
	Register a class as MQ manager.
	:param cls: Class which implements MQ functionality
	"""
	MQ_MANAGERS[cls.SCHEME] = cls
	return cls


@message_queue
class RabbitMQManager:
	SCHEME = 'rabbitmq'  # MQ managers are identified by their scheme.
	SNAPSHOT_FIELDS = PARSABLE_FIELDS

	def __init__(self, host=None, port=None, fields=None *, connection=None, channel=None, pika=pika):
		"""
		Manages communication to remote queue.
		The host can be given in few ways:
		host, port - The address of the message queue
		connection - Connection object to the remote host.
		channel - Direct channel to the MQ.
		Optional - Injecting different pika module, which supports the same API as used here.
		"""
		self.host = host
		self.port = port
		self.connection = connection
		self.channel = channel
		self.pika = pika

		if channel is not None:
			self._bind_methods()
			return

		if connection is not None:
			self.connect(connection=connection)
			return

		if port is not None and host is not None:
			self.connect(host, port)

	def connect(self, host=None, port=None, connection=None):
		"""
		Create a connection object if no such is given, using the host, port
		Get a channel to communicate with remote MQ
		:param host: IP address of the remote/local host which runs the MQ
		:param port: Port which the MQ listens to.
		:param connection: prebuilt connection object can be given instead
		"""
		if connection is None:
			if host is None or port is None:
				raise ValueError('The method needs either connection object, or host, port in order to connect')
			self.host = host
			self.port = port
			params = self.pika.ConnectionParameters(host, port)
			connection = self.pika.BlockingConnection(params)
		self.connection = connection
		self.channel = connection.channel()
		self._bind_methods()

	def _bind_methods(self):
		"""
		Exports the API of the MQ.
		Thus giving full control to the user, in addition to this very purpose-specific API.
		"""
		methods = ['queue_declare', 'exchange_declare', 'queue_bind']
		for method in methods:
			setattr(self, method, getattr(self.channel, method))

	def _build_exchanges(self, fields):
		for field in self.SNAPSHOT_FIELDS:
			self.channel.exchange_decalre(exchange=field, exchange_type='fanout')

	def queue_snapshot(self, user, snapshot):
		"""
		Queuing a Snapshot to some queue in the remote MQ.
		:param user: The user which uploaded the snapshot.
		:param snapshot: Snapshot dictionary with the attributes to upload.
		"""
		pass

	def close(self):
		if self.connection is not None:
			self.connection.close()
# TODO: Lecture 3A min 22:44
