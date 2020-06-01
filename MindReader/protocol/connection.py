import logging

from .. import IOAccess

logger = logging.getLogger('connection')


class Connection:
	PROTOCOL_SCHEME = 'http'
	GET_CONFIG = '/fields'
	UPLOAD_SNAPSHOT = '/snapshot'
	REGISTER = '/register'
	# User must contain those fields, can also be configurable if future changes demands it
	USER_MUST_FIELDS = ['user_id', 'username']
	MAX_TRIES = 3

	def __init__(self, domain, user):
		self.domain = domain.split('://', 1)[-1]  # Remove http prefix if exist
		self.url_basis = self.PROTOCOL_SCHEME + '://' + self.domain
		self.fields = None
		if any(field not in user for field in self.USER_MUST_FIELDS):
			logger.error('User had a missing field')
			raise ValueError('Invalid user')
		logger.info(f'New connection created to host {self.url_basis}')

		self.register_user(user)
		self.user = user

	def register_user(self, user):
		"""
		Register a user to the server, and get fields available
		:param user: User dict.
		"""
		logger.info('Registering user....')
		headers = {'Content-Type': 'application/json'}

		try:
			response = IOAccess.write_url(self.url_basis + self.REGISTER, 'user', user, version='json',
			                              driver_kwargs={'mode': 'w', 'headers': headers})
			if response.status_code != 200:
				raise ValueError(f'The server returned {response.status_code} - {response.text}')
		except Exception as e:
			logger.error(e)
			raise ConnectionError(f'Couldn\'t upload user to {self.url_basis + self.REGISTER}')

		self.fields = response.json()
		logger.info('User registered')
		logger.debug(f'The accepted fields by the server are {self.fields}')

	def upload(self, snapshot):
		"""
		Uploads a single snapshot using HTTP REST API.
		:param snapshot: Snapshot object which holds in it's attributes the different fields.
		"""
		logger.debug('Uploading a snapshot')
		# Since there is no alternative format for now this is fine, in the future this can be easily converted to
		# a configurable attribute
		headers = {'UserId': str(self.user['user_id']), 'Content-Type': 'application/protobuf'}
		driver_kwargs = {'headers': headers, 'mode': 'wb'}
		response = IOAccess.write_url(self.url_basis + self.UPLOAD_SNAPSHOT, 'snapshot', snapshot,
		                              driver_kwargs=driver_kwargs, version='protocol_protobuf', fields=self.fields)

		if response.status_code == 200:
			logger.debug('Snapshot was successfully uploaded')
			return
		logger.error(f'The server returned {response.status_code} - {response.text}')
		raise ConnectionError('Couldn\'t upload snapshot')
