import io
import logging
from pathlib import Path

import click

from .utils import listener, log_error
from . import utils
from . import IOAccess, MessageQueue
from .defaults import SERVER_DEFAULT_HOST, SERVER_DEFAULT_PORT, DATA_DIR

logger = logging.getLogger('server')


###############################
# CLI functions
###############################


@click.group()
@click.option('--debug', is_flag=True)
@click.option('--no-logging', is_flag=True)
def cli(debug, no_logging):
	utils.logging_level = logging.INFO
	if debug:
		utils.logging_level = logging.DEBUG

	if no_logging:
		logging.disable()


@cli.command(name='run-server')
@click.argument('mq-url')
@click.option('-h', '--host', default=SERVER_DEFAULT_HOST, help='Host to bind')
@click.option('-p', '--port', default=SERVER_DEFAULT_PORT, type=int)
@click.option('--data-dir', help='Where to store snapshot for further analysis', default=DATA_DIR)
def cli_run_server(mq_url, host, port, data_dir):
	"""
	Listens for snapshot uploads via HTTP:POST requests.
	publishes them to the message queue on MQ-URL.
	"""
	logger.info('Starting server from CLI')
	logger.debug(f'Everything should be stored to {data_dir} directory')
	data_dir = Path(data_dir)
	mq = MessageQueue.MessageQueue(mq_url)

	def user_publisher(*args):
		return handle_user(*args, mq)

	def snapshot_publisher(*args):
		return handle_snapshot(*args, data_dir, mq)

	run_server_publisher(host, port, user_publisher, snapshot_publisher)

	mq.close()


run_server = cli_run_server.callback


##########################
# Main functionality
##########################

@log_error(logger)
def run_server_publisher(host, port, publish_user=None, publish_snapshot=None):
	"""
	Run a server which listens on host:port.
	The server receives every user and snapshots, and publishes them with given handlers.
	:param publish_user: What to do with each given user. Default is NOP.
	:param publish_snapshot: What to do with each given snapshot. Default is printing
	Both publishers can return answer for the server to answer or None for 200, OK
	"""
	listener.config_publishers(publish_user, publish_snapshot)
	try:
		listener.listener(host, port)
	except KeyboardInterrupt:
		logging.info('Got SIGINT Exiting...')


#######################
# PUBLISH FUNCTIONS
#######################

def handle_snapshot(user_id, snapshot, data_dir, mq):
	raw_snapshot, snapshot_type = snapshot['data'], snapshot['type']
	if snapshot_type not in IOAccess.READERS_MIME_TYPE['snapshot']:
		return 'The given type is unsupportable', 400

	version = IOAccess.READERS_MIME_TYPE['snapshot'][snapshot_type]

	logger.info(f'Server publishes a new snapshot of type {version}')

	snapshot_raw_path = data_dir / user_id / str(utils.next_snapshot_id()) / f'snapshot.raw.{version}'

	logger.info('Creating new directory to the snapshot')
	logger.debug(f'Directory path is {data_dir}')

	snapshot_raw_path.parent.mkdir(exist_ok=True, parents=True)

	logger.info(f'The snapshot is being saved to file')
	logger.debug(f'Snapshot file path is {snapshot_raw_path}')

	with open(snapshot_raw_path, 'wb') as fd:
		fd.write(raw_snapshot)

	mq.publish_snapshot(str(snapshot_raw_path))

	logger.info('Sever published the snapshot successfully')


def handle_user(user, mq):
	user_data, user_type = user['data'], user['type']
	if user_type not in IOAccess.READERS_MIME_TYPE['user']:
		logger.debug(f'The given data type was {user["type"]}')
		return 'The given type is not supported', 400

	version = IOAccess.READERS_MIME_TYPE['user'][user_type]  # Get the version type

	with io.StringIO(user_data) as fd:
		logger.debug('Parsing user...')
		user = IOAccess.read(fd, 'user', version=version)
	logger.debug('Publishing user to mq...')
	mq.publish_user(user)
	logger.debug('User has been published')


if __name__ == '__main__':
	cli()
