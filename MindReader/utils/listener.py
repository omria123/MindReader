from io import StringIO
import json

from flask import Flask, request, session
from flask_session import Session

from .reader import read_object

app = Flask(__name__)
SESSION_TYPE = 'redis'  # TODO: access by yaml file.
app.config.from_object(__name__)  # TODO : change this.
Session(app)

PARSABLE_FIELDS = []  # TODO: Change to dynamically construction
USERS = {}  # USER_ID-TO-USER_MAPPING

DEFAULT_HOST = '127.0.0.1'  # TODO: change to fetch from yaml.
DEFAULT_PORT = 8080

handle_snapshot = None


@app.route('/snapshot', methods=['POST'])
def upload_snapshot():
	"""
	Receive the client's snapshot
	:return:
	"""
	headers, body = request.headers, request.data
	user_id = session.get('UserId')
	if user_id is None:
		return 'You have to login_server in order to upload snapshot', 401
	if user_id not in USERS:
		return 'Your cookie isn\'t valid any more', 401

	snapshot = read_object(StringIO(body), obj='snapshot_protocol', scheme='obj')

	handle_snapshot(USERS[user_id], snapshot)
	return 'Thanks!!!', 200


@app.route('/login_server', methods=['POST'])
def login():
	"""
	POST /login_server handler.
	This URL handle new users who would like to upload snapshots.
	This function[ saves the user's info and grant it a session token,
	which should be used later for uploading snapshots.
	:return: The fields available to be parsed in server side.
	"""
	user = read_object(request, scheme='obj', obj='user')
	session['UserId'] = user.user_id
	USERS[user.user_id] = user
	return json.dumps(PARSABLE_FIELDS), 200


def listener(publish):
	global handle_snapshot
	handle_snapshot = publish
	app.run()
