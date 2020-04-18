from .writer import write_object


class Connection:
	PROTOCOL_SCHEME = 'http'
	GET_CONFIG = '/fields'
	UPLOAD_SNAPSHOT = '/snapshot'
	LOGIN = '/login_server'

	def __init__(self, domain, user):
		self.domain = domain
		self.url_basis = self.PROTOCOL_SCHEME + '://' + self.domain
		self.session_cookie = None
		self.fields = None
		self.login_server(user)

	def login_server(self, user):
		response = write_object(self.url_basis + self.LOGIN, user, obj='user')
		self.fields = response.json()
		self.session_cookie = response.headers['Set-Cookie'].split(';')[0].strip()

	def upload(self, snapshot):
		headers = {'Cookie': self.session_cookie}
		write_object(self.url_basis + self.UPLOAD_SNAPSHOT, snapshot, headers=headers,
		             obj='snapshot_protocol', write_format='protobuf')
