"""
Apologies for the horrible code in this module, I am new to web programming,
and it's have been frustrating to handle some of the concepts here.
"""

import datetime as dt
import functools
import io
import itertools
import logging
import random

import click
import pathlib
from flask import Flask, jsonify, request, redirect, render_template, send_file
from flask_cors import CORS
import timeago

from .utils import log_error, HTTP_HEADERS
from .Database import Database
from . import IOAccess
from .defaults import API_DEFAULT_PORT, API_DEFAULT_HOST

app = Flask(__name__)
CORS(app)
logger = logging.getLogger('API')

MAX_POSTS = 30
database_handler = None
cur_dir = str(pathlib.Path(__file__).parent)

# SOURCES
brains = [f'/static/brains/brain{x}_tn.jpg' for x in range(1, 5)]
cards = [
	"card border-primary",
	"card border-secondary",
	"card border-success",
	"card border-danger",
	"card border-warning",
	"card border-info",
	"card border-light",
	"card border-dark"]


########################
# CLI ACCESS
########################
@click.group()
def cli():
	pass


@cli.command(name='run-api-server')
@click.option('-h', '--host', 'host', default=API_DEFAULT_HOST)
@click.option('-p', '--port', 'port', default=API_DEFAULT_PORT, type=int)
@click.argument('database')
def cli_run_api_server(host, port, database):
	"""
	Runs the server to access the DATABASE
	"""
	global database_handler
	logging.getLogger('werkzeug').disabled = True  # Don't want the weird Flask logger

	logger.debug(f'Connecting to DB {database}')
	database_handler = Database(database)
	logger.info(f'Start listening on {host}:{port}')
	app.run(host=host, port=port)


run_api_server = cli_run_api_server


######################
# HELPERS
######################

def handle_db_fail(log):
	"""
	Assuming that the callback depends only on the database.
	In case of failure, an appropriate response and logging (using log) is given. (Basically blaming the DB)
	"""

	def decorator(f):
		@functools.wraps(f)
		def wrapper(*args, **kwargs):
			try:
				return f(*args, **kwargs)
			except Exception as e:
				log.error(e)
				return 'Something is wrong with the database', 503

		return wrapper

	return decorator


def bound_amount(l, bound=MAX_POSTS):
	counter = 0
	if 'counter' in request.args:
		counter = int(request.args['counter'])

	if counter + bound < len(l):
		return l[counter: counter + bound]
	else:
		return l[counter:]


def db_not_found(user, snapshot=1, result=1):
	if user is None:
		logger.debug('The user doesn\'t exists')
		return f'No such user in the db', 404
	if snapshot is None:
		logger.debug('The user has no such snapshot')
		return f'The user has no such snapshot in the db', 404
	if result is None:
		logger.debug('The snapshot has no such result name')
		return f'The requested result doesn\'t exist', 404


########################
# API PATHS
########################


@app.route('/users')
@handle_db_fail(logger)
def get_users():
	logger.debug('List of the users has been requested')

	def basic_user_info(user):
		return {
			'username': user['username'],
			'user_id': user['user_id']
		}

	return jsonify(list(map(basic_user_info, database_handler.get_users())))


@app.route('/users/<user_id>')
@handle_db_fail(logger)
def get_user(user_id):
	logger.debug(f'User {user_id} has been requested')
	user_details = database_handler.get_user(user_id)
	return db_not_found(user_details) or jsonify(user_details)


@app.route('/users/<user_id>/snapshots')
@handle_db_fail(logger)
def get_snapshots(user_id):
	logger.debug(f'Snapshot list user with {user_id=} ')
	snapshots = database_handler.get_snapshots(user_id)

	def extract_basic_info(snapshot):
		return {
			'timestamp': snapshot['timestamp'],
			'user_id': snapshot['user_id'],
			'snapshot_id': snapshot['snapshot_id']
		}

	return db_not_found(snapshots) or jsonify(list(map(extract_basic_info, snapshots)))


@app.route('/users/<user_id>/snapshots/<snapshot_id>')
@handle_db_fail(logger)
def get_snapshot(user_id, snapshot_id):
	logger.debug(f'Snapshot has been requested for {user_id=}, {snapshot_id=}')

	def extract_metadata(full_snapshot):
		return {
			'timestamp': full_snapshot['timestamp'],
			'user_id': full_snapshot['user_id'],
			'snapshot_id': full_snapshot['snapshot_id'],
			'results': list(full_snapshot['result'].keys()),
		}

	user, snapshot = database_handler.get_snapshot(user_id, snapshot_id)
	return db_not_found(user, snapshot) or jsonify(extract_metadata(snapshot))


@app.route('/users/<user_id>/snapshots/<snapshot_id>/<result_name>')
@log_error(logger)
def get_snapshot_result(user_id, snapshot_id, result_name):
	logger.debug(f'Snapshot\'s {result_name} for {user_id=}, {snapshot_id=}  has been requested')
	user, snapshot, result = database_handler.get_snapshot_result(user_id, snapshot_id, result_name)
	return db_not_found(user, snapshot, result) or jsonify(result)


@app.route('/users/<user_id>/snapshots/<snapshot_id>/<result_name>/data')
@handle_db_fail(logger)
def get_snapshot_result_data(user_id, snapshot_id, result_name):
	logger.debug(f'Snapshot\'s data has been requested for {user_id=}, {snapshot_id=}, {result_name=}')

	user, snapshot, result = database_handler.get_snapshot_result(user_id, snapshot_id, result_name)

	response = db_not_found(user, snapshot, result)
	if response is not None:
		return response

	headers = {key: result['metadata'][key] for key in result['metadata'] if key in HTTP_HEADERS}
	with IOAccess.open(result['location'], mode='rb') as fd:
		return fd.read(), 200, headers


########################
# GUI PATHS
########################


@app.route('/')
@log_error(logger)
def index():
	all_users = database_handler.get_users()
	logger.info('New access to index page')
	if len(all_users) == 0:
		return render_template('empty.html')
	nums = list(range(len(all_users)))
	fields = sorted(list(all_users[0].keys()))  # The choice of user doesn't matter
	all_users.sort(key=lambda user: int(user['user_id']))

	def repr_user(user):
		genders = {0: 'Male', 1: 'Female', 2: 'Other'}
		user['gender'] = genders[user['gender']]
		user['birthday'] = dt.datetime.fromtimestamp(user['birthday']).strftime('%d.%m.%Y')
		return user
	all_users = list(map(repr_user, all_users))

	return render_template('index.html', fields=fields, users=all_users, nums=nums, title='', phrase='')


@app.route('/user')
@log_error(logger)
def user_page():
	logger.info('Some user page was requested')
	if 'user_id' not in request.args:
		logger.debug('No id was given')
		return redirect('/')
	user_id = request.args['user_id']
	user = database_handler.get_user(user_id)

	snapshots = database_handler.get_snapshots(user_id)

	response = db_not_found(snapshots)

	if response is not None:
		return response
	amount = database_handler.get_snapshots_amount(user_id)
	page = 1

	if 'page' in request.args:
		page = int(request.args['page'])

	snapshots = itertools.islice(snapshots, (page - 1) * MAX_POSTS, page * MAX_POSTS)

	def format_snapshot(snapshot):
		epoch_time = int(snapshot['timestamp']) / 1000
		st_time = timeago.format(dt.datetime.fromtimestamp(epoch_time), dt.datetime.now())
		# Convert to time ago.
		return {
			'snapshot_id': snapshot['snapshot_id'],
			'timestamp': st_time,
			'results': list(snapshot['result'].keys()),
			'funny': random.choice(brains)
		}

	result_snapshots = list(map(format_snapshot, snapshots))
	return render_template('user.html',
	                       username=user['username'],
	                       user_id=user['user_id'],
	                       snapshots=result_snapshots,
	                       page=page, next_page=page * MAX_POSTS < amount)


@app.route('/snapshot')
def view_snapshot():
	if 'snapshot_id' not in request.args or 'user_id' not in request.args:
		return redirect('/')

	user_id, snapshot_id = request.args['user_id'], request.args['snapshot_id']
	user, snapshot = database_handler.get_snapshot(user_id, snapshot_id)

	response = db_not_found(user, snapshot)
	if response is not None:
		return response

	epoch_time = int(snapshot['timestamp']) / 1000  # ms to s
	time_diff = timeago.format(dt.datetime.fromtimestamp(epoch_time), dt.datetime.now())
	return render_template('snapshot.html', user_id=user_id, username=user['username'], snapshot=snapshot,
	                       timeago=time_diff, pick_card=lambda: random.choice(cards))


@app.route('/search')
@log_error(logger)
def search():
	if 'phrase' in request.args:
		phrase = request.args['phrase']
	else:
		return 'No phrase was given', 400
	all_users = list(filter(lambda u: (phrase in u['username']), database_handler.get_users()))

	logger.info(f'New search request, phrase - {phrase}')

	if len(all_users) == 0:
		return render_template('empty.html')

	nums = list(range(len(all_users)))

	fields = sorted(list(all_users[0].keys()))  # The choice of user doesn't matter
	all_users.sort(key=lambda user: int(user['user_id']))

	return render_template('index.html', fields=fields, users=all_users, nums=nums, title=' - search', phrase=phrase)


@app.route('/static/brains/<image_name>')
@log_error(logger)
def brain(image_name):
	with open(f'{cur_dir}/static/brains/{image_name}', 'rb')as fd:
		image_binary = fd.read()
	return send_file(io.BytesIO(image_binary), mimetype='imgae/jpeg')


@app.route('/load_users')
@log_error(logger)
def load_users():
	phrase = ''
	if 'phrase' in request.args:
		phrase = request.args['phrase']

	return jsonify([user for user in database_handler.get_users() if phrase in user['username']])


if __name__ == '__main__':
	cli()
