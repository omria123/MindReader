from io import StringIO, BytesIO

import pytest
import requests

from MindReader.utils import Drivers


######################
# API TESTS
######################
@pytest.mark.parametrize('scheme,driver', Drivers.driver_manager._drivers.items())
def test_find_driver(scheme, driver):
	assert Drivers.find_driver(scheme) == driver


@pytest.mark.parametrize('name', ['hola', 'bola', 'cola', 124, b'Omri'])
def test_driver_decorator(name):
	obj = object()
	Drivers.driver(name)(obj)
	assert Drivers.find_driver(name) is obj


######################
# DRIVERS
######################
def find_mode(data, basic_mode):
	if type(data) is bytes:
		return basic_mode + 'b'
	return basic_mode


######################
# Object_driver
######################


@pytest.mark.parametrize('fd', [StringIO('hello'), BytesIO(b'test'), BytesIO((2 << 16) * b'A')])
def test_object_driver_cm(fd):
	object_driver = Drivers.find_driver('obj')
	with object_driver(fd) as new_fd:
		assert new_fd is fd


@pytest.mark.parametrize('fd', [StringIO('hello'), BytesIO(b'test'), ])
def teat_object_driver(fd):
	object_driver = Drivers.find_driver('obj')
	new_fd = object_driver(fd)
	assert new_fd.write == fd.read
	assert new_fd.read == fd.read
	assert new_fd.close() is fd


'''
requests's Requirements:
- requests.codes
- requests.get(url, headers) -> response
- requests.post(url, headers, body) -> response
The response's requirements:
- status_code: 200 -> OK, else -> Env
- All other attributes should of response also all non-private's belong    
'''


class MockResponse:
	def __init__(self, status_code):
		self.status_code = status_code

	def __call__(self, url, headers=None, body=None):
		self.url = url
		self.headers = headers
		self.body = body

	def special_method(self):
		pass


class RequestsTemplate:
	pass


@pytest.fixture(params=[
	MockResponse(200), MockResponse(404), MockResponse(300)
])
def fake_requests(request):
	module = RequestsTemplate
	module.codes = requests.codes

	def get(url, headers=None):
		return request.param(url, headers)

	def post(url, headers=None, body=None):
		return request.param(url, headers, body)

	module.get = get
	module.post = post
	return module


######################
# HTTP Driver
######################
http_driver = Drivers.find_driver('http')


@pytest.fixture(params=[

])
@pytest.mark.parametrize('url,mode,headers', [
	(, ,),
	(, ,),
	(, ,)
])
def test_http_driver_write(fake_requests, url, mode, headers, bodies):
	fd = http_driver(url, mode, headers, requests=fake_requests)
	for body in bodies:
		fd.write(body)
	response = fd.flush()
	assert response. == ''.join(bodies)

	for body in bodies ==
	assert fd.close()


def test_http_driver_write_headers():
	pass


def test_http_driver_write_headers2():
	# Testing the write headers thorough write functionality
	pass


def


def test_http_driver_read(fake_requests):
	pass


def test_http_driver_cm(fake_requests):
	pass
