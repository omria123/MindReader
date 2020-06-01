import logging

from flask import Flask, request, jsonify

from ..IOAccess import READERS_MIME_TYPE
from ..parsers import PARSERS
from ..utils import log_error

app = Flask(__name__)


###################
# DEFAULT
###################
def handle_snapshot(user_id, snapshot):
	print(snapshot['data'])


def handle_user(user):
	pass


logger = logging.getLogger('listener')


@app.route('/snapshot/types')
@log_error(logger)
def snapshot_types():
	"""
	Return supportable mime-types for uploading snapshot
	"""
	logger.debug('Got request for /snpashot/types')
	return jsonify(READERS_MIME_TYPE['snapshot'].values())


@app.route('/user/types')
@log_error(logger)
def user_types():
	"""
	Return supportable mime-types for uploading snapshot
	"""
	return jsonify(READERS_MIME_TYPE['snapshot'].values())


@app.route('/snapshot', methods=['POST'])
@log_error(logger)
def upload_snapshot():
	"""
	Receive the client's snapshot in body and use the handle function to publish_snapshot it else-where.
	Fatal: Must register the user before calling this function.
	"""

	headers, body = request.headers, request.get_data()
	logger.debug(f'New snapshot arrived in encoding {request.mimetype} with length of {len(request.data)}')

	if 'UserId' not in headers:
		logger.debug('No user id has been given, rejecting...')
		return 'The request must mention the user\'s id in the UserId header.', 400

	logger.debug('Sending snapshot to handler')

	result = handle_snapshot(headers["UserId"], {'data': body, 'type': request.mimetype})

	if result is None:
		logger.debug('Snapshot successfully uploaded')
		return 'OK', 200
	logger.debug('The snapshot is invalid')
	return result


@app.route('/register', methods=['POST'])
@log_error(logger)
def register():
	"""
	POST /register handler.
	The function receives a User in the body of the request, in JSON format.
	Then it transfer it to further processing to handle_user.
	This can be easily turn into selective user handling, i.e. only premium clients can send
	certain fields. Or maybe adding authentication to avoid DoS attack.
	"""

	headers, body = request.headers, request.get_data().decode()
	logger.debug(f'User received in format {request.mimetype}')
	result = handle_user({'data': body, 'type': request.mimetype})

	if result is None:
		logger.debug('User registered sending fields')
		return jsonify(list(PARSERS.keys()) ), 200

	logger.debug('The user is invalid, rejecting registration...')
	return result


def config_publishers(user_publisher=None, snapshot_publisher=None):
	global handle_user, handle_snapshot
	logger.debug('Configuring user, snapshot handlers')
	handle_user = user_publisher or handle_user
	handle_snapshot = snapshot_publisher or handle_snapshot


def Listener(host, port):
	"""
	Starts a listener, which accepts snapshots and users.
	:param host: IP to bind the server to.
	:param port: Port to bind to
	"""

	logger.info(f'Listening on {host}:{port}')
	logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
	try:
		app.run(host, port)
	except KeyboardInterrupt:
		logger.info('SIGINT sent exiting...')
