from io import BytesIO, StringIO
import logging

import requests

from ..manager import driver
from ... import utils  # For

logger = logging.getLogger('http_driver')
utils = utils  # Ignore warning for not using, only importing to run the logging setup


@driver('http')
class HTTPDriver:
	"""
	Driver abstracting
	"""
	SCHEME = 'http://'

	def __init__(self, url, mode, headers=None, *, requests=requests):
		"""
		Initialize Driver for writing and reading from remote HTTP server.
		:param url: URL to access the server (Should be as  host/URI
		:param mode: 'r' or 'w' i.e. GET or POST. if 'b' is set data is accessed as binary.
		:param headers: Optional - Headers to give the request.
		:param requests: Optional - Injected 'requests' module
		"""
		self.url = self.SCHEME + url.split('://', 1)[-1]
		self.mode = mode
		self.headers = {} if headers is None else headers
		self.body = BytesIO() if 'b' in mode else StringIO()
		self.requests = requests

		if 'r' not in mode:
			logger.info('New POST file is open')
			logger.debug(f'URL={self.url}')

		else:
			logger.info('New GET file is open')
			self.response = self.requests.get(self.url, headers=self.headers)
			logger.debug(f'URL={self.url}, body size- {len(self.response.text)}')

			if 'b' in mode:
				self.body = BytesIO(self.response.text.encode())
			else:
				self.body = StringIO(self.response.text)
		self.read = self.body.read
		self.seek = self.body.seek
		self.tell = self.body.tell

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()

	def write(self, data):
		"""
		The functionality varies according to different types of data:
		str/bytes (should fit the Driver's mode) - Writes the data to the body of the request.
		Otherwise treats it as writing of headers.
		"""
		if type(data) in (list, dict, tuple):
			return self.write_headers(data)
		return self.body.write(data)

	def write_headers(self, headers):
		"""
		Update the headers of the request by the value of the headers.
		:param headers: The headers which should be updated. Can be a tuple of single header or a dict of few.
		"""
		if type(headers) is tuple:
			self.headers[headers[0]] = headers[1]
		if type(headers) is list:
			headers = dict(headers)
		if type(headers) is dict:
			self.headers.update(headers)

	def __getattr__(self, attr):
		"""
		Delegating attribute fetching to the response obj_name, for full access to the information about
		the request (available and needed only in read mode)
		:param attr: attr to search
		"""
		if 'r' not in self.mode:
			raise AttributeError(f"'{self.__class__.__name__}' obj_name has no attribute '{attr}'")

		return getattr(self.response, attr)

	# Write mode only methods
	def flush(self, *, keep_headers=False, keep_body=False):
		"""
		Take all the buffered data so far and send to with post to remote host
		:param keep_headers: Should I keep the headers for next flush?
		:param keep_body: Should I keep the body for next flush?
		"""
		logger.debug(f'Sending POST to {self.url} with body of size {len(self.body.getvalue())}')
		self.response = self.requests.post(self.url, data=self.body.getvalue(), headers=self.headers)
		logger.debug(f'The length of the response is {len(self.response.text)}')
		if not keep_body:
			self.body = BytesIO() if 'b' in StringIO() else ''
		if not keep_headers:
			self.headers = {}
		return self.response

	def close(self):
		"""
		Simple close function.
		"""
		if 'w' not in self.mode:  # Read mode does nothing
			return
		return self.flush(keep_headers=True)

	def __repr__(self):
		method = 'GET'
		if 'w' in self.mode:
			method = 'POST'
		return f'HTTPDriver(url={self.url}, {method=})',

	def __str__(self):
		return self.url
