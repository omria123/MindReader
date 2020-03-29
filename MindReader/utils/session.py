class Session(object):
	CLIENT = 0
	SERVER = 1

	# SESSIONS STATES:
	CREATED = 0  # After __init__
	STOP = 1  # Connection closed
	SNAPSHOT = 2  # got a snapshot

	def __init__(self, conn, config, side):
		self.connection = conn
		self.config = config
		self.side = side
		self._state = self.CREATED

	@classmethod
	def client(cls, conn, config):
		s = cls(conn, config, cls.CLIENT)
		s._setup_client()
		return s

	@classmethod
	def server(cls, conn):
		return cls(conn, None, cls.SERVER)

	def _setup_client(self):
		pass

	def send_user(self, user):
		pass

	def send_snapshot(self, snapshot):
		pass

	def proceed(self):
		pass

	def close(self):
		self.connection.close()

	def v2_encoder(self, obj):
		pass

	def v2_decoder(self, obj):
		pass
