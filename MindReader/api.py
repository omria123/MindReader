import functools
import logging

import click
from flask import Flask, jsonify, request, redirect, url_for, g, render_template

from .utils import log_error
from . import IOAccess
from .defaults import API_DEFAULT_PORT, API_DEFAULT_HOST

app = Flask(__name__)

logger = logging.getLogger('API')

MAX_POSTS = 20


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

	g.database = database
	logging.getLogger('werkzeug').disabled = True  # Don't want the weird Flask logger
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


########################
# API PATHS
########################


@app.route('/users')
@handle_db_fail(logger)
def get_users():
	logger.info('List of the users has been requested')
	return jsonify(g.database.get_users()), 200


@app.route('/users/<user_id>')
@handle_db_fail(logger)
def get_user(user_id):
	logger.info('User has been requested')
	logger.debug(f'{user_id=}')
	user_details = g.database.get_user(user_id)

	if user_details is None:
		logger.debug('The user doesn\'t exists')
		return f'No user with user id {user_id}', 404
	return user_details, 200


@app.route('/users/<user_id>/snapshots')
@handle_db_fail(logger)
def get_snapshots(user_id):
	logger.info('User\'s snapshot list has been requested')
	logger.debug(f'{user_id=}')

	snapshots = g.database.get_snapshots(user_id)

	if snapshots is None:
		logger.debug('The user doesn\'t exists')
		return f'No user with user id {user_id}', 404
	return jsonify(snapshots), 200


@app.route('/users/<user_id>/snapshots/<snapshot_id>')
@handle_db_fail(logger)
def get_snapshot(user_id, snapshot_id):
	logger.info('Snapshot has been requested')
	logger.debug(f'{user_id=}, {snapshot_id=}')

	user, snapshot = g.database.get_snapshot(user_id, snapshot_id)
	if user is None:
		logger.debug('The user doesn\'t exists')
		return f'No user with user id {user_id}', 404
	if snapshot is None:
		logger.debug('The user has no such snapshot')
		return f'The user has no such snapshot with id {snapshot_id}', 404
	return jsonify(snapshot), 200


@app.route('/users/<user_id>/snapshots/<snapshot_id>/<result_name>')
@log_error(logger)
def get_snapshot_result(user_id, snapshot_id, result_name):
	logger.info('Snapshot\'s result data has been requested')
	logger.debug(f'{user_id=}, {snapshot_id=}, {result_name=}')
	user, snapshot, result = g.database.get_snapshot_result_data(user_id, snapshot_id, result_name)
	if user is None:
		logger.debug('The user doesn\'t exists')
		return f'No user with user id {user_id}', 404
	if snapshot is None:
		logger.debug('The user has no such snapshot')
		return f'The user has no such snapshot with id {snapshot_id}', 404
	if result is None:
		logger.debug('The snapshot has no such result name')
		return f'The snapshot has no available {result_name} binary data', 404
	return jsonify(result)


@app.route('/users/<user_id>/snapshots/<snapshot_id>/<result_name>/data')
@handle_db_fail(logger)
def get_snapshot_result_data(user_id, snapshot_id, result_name):
	logger.info('Snapshot\'s result has been requested')
	logger.debug(f'{user_id=}, {snapshot_id=}, {result_name=}')

	user, snapshot, result = g.database.get_snapshot_result_data(user_id, snapshot_id, result_name)

	if user is None:
		logger.debug('The user doesn\'t exists')
		return f'No user with user id {user_id}', 404

	if snapshot is None:
		logger.debug('The user has no such snapshot')
		return f'The user has no such snapshot with id {snapshot_id}', 404

	if result is None:
		logger.debug('The snapshot has no such result name')
		return f'The snapshot has no available {result_name}', 404

	with IOAccess.open(result[result_name]['location'], mode='rb') as fd:
		return fd.read(), 200


########################
# GUI PATHS
########################

@app.route('/')
def index():
	logger.info('New access to index page')
	return render_template('index.html')


@app.route('/user')
def user_page():
	logger.info('Some user page was requested')
	if 'id' not in request.args:
		logger.debug('No id was given')
		return redirect(url_for('index'))
	user_id = request.args['id']
	user_data = g.database.get_user(user_id)
	if user_data is None:
		logger.debug('The requested user doesn\'t exists')
		return "The user doesn't exist", 404

	logger.debug(f'Returning user with {user_id=}, username={user_data["username"]}')
	return user_data.foramt(user_data)


@app.route('/search')
def search():
	return render_template('search.html')


@app.route('/load')
def load():
	phrase = ''
	if 'phrase' in request.args:
		phrase = request.args['phrase']
	users = get_users()
	return jsonify(bound_amount([(name, uid) for name, uid in users if phrase in name]))


if __name__ == '__main__':
	cli()
