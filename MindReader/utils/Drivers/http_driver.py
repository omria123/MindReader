from io import BytesIO, StringIO

import requests

from . import driver


@driver('http')
class HTTPDriver:
	"""
	Driver for reading and writing from remote HTTP server. (Available also as context manager)
	Reading - Given a URL, sending GET request and read file from remote host.
	Then the object will export all the available functionality of the response. (Using getattr)
	The read functionality is still available, and reads directly from the body of the response.

	Writing - returning a fake file which collects the body of the post request

	This Driver interface has few more features which helps to gain more access to aspects of the communication:
	(Which means this is no regular driver, since it's expands the API of normal driver
	instance.response - Once every request is sent, the response is exported via this attribute.
	flush - Send the request which is available so far (apply to  write mode only).
	writing headers -  Can be done though write_headers or even though the native write, by sending it non string/bytes
	object.
	"""
	SCHEME = 'http://'

	def __init__(self, url, mode, headers=None, *, requests=requests):
		"""
		Initialize driver for writing and reading from remote HTTP server.
		:param url: URL to access the server (Should be as  host/URI
		:param mode: 'r' or 'w' i.e. GET or POST. if 'b' is set data is accessed as binary.
		:param headers: Optional - Headers to give the request.
		:param requests: Optional - Injected 'requests' module
		"""
		self.url = url
		self.mode = mode
		self.headers = {} if headers is None else headers
		self.body = b'' if 'b' in mode else ''
		self.requests = requests

		if 'r' not in mode:
			return

		self.response = self.requests.get(url, headers=self.headers)
		if self.response.status_code != requests.codes['OK']:
			raise EnvironmentError('Couldn\'t Receive file from remote location')
		if 'b' in mode:
			body = BytesIO(self.response.text.encode())
		else:
			body = StringIO(self.response.text)
		self.read = body.read

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()

	def write(self, data):
		"""
		The functionality varies according to different types of data:
		str/bytes (should fit the driver's mode) - Writes the data to the body of the request.
		Otherwise treats it as writing of headers.
		"""
		if type(data) in (list, dict):
			return self.write_headers(data)
		self.body += data

	def write_headers(self, headers):
		"""
		Update the headers of the request by the value of the headers.
		:param headers: The headers which should be updated. Can be a tuple of single header or a dict of few.
		"""
		if type(headers) is tuple:
			self.headers[headers[0]] = headers[1]
		if type(headers) is dict:
			self.headers.update(headers)

	def __getattr__(self, attr):
		"""
		Delegating attribute fetching to the response object, for full access to the information about
		the request (available and needed only in read mode)
		:param attr: attr to search
		"""
		if 'r' not in self.mode:
			raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")

		return getattr(self.response, attr)

	# Write mode only methods
	def flush(self, *, keep_headers=False, keep_body=False):
		"""
		Take all the buffered data so far and send to with post to remote host
		:param keep_headers: Should I keep the headers for next flush?
		:param keep_body: Should I keep the body for next flush?
		"""

		self.response = self.requests.post(url=self.SCHEME + self.url, data=self.body, headers=self.headers)
		if not keep_body:
			self.body = b'' if 'b' in self.mode else ''
		if not keep_headers:
			self.headers = {}
		return self.response

	def close(self):
		"""
		Simple close function.
		On case of 'w' flushes all data.
		"""
		if 'w' in self.mode:
			return self.flush(keep_headers=True)
