import itertools
import logging

import click

from .defaults import SERVER_DEFAULT_HOST, SERVER_DEFAULT_PORT
from .IOAccess import object_readers, read_url, DRIVERS
from .protocol import Connection
from .utils import log_error

logger = logging.getLogger('client')
available_schemes = list(DRIVERS.keys())
available_schemes.remove('object')


@click.group()
@click.option('--no-logging', is_flag=True)
def cli(no_logging):
	if no_logging:
		logging.disable()


@cli.command(name='upload-sample')
@click.argument('path')
@click.option('-h', '--host', 'host', default=SERVER_DEFAULT_HOST)
@click.option('-p', '--port', 'port', default=SERVER_DEFAULT_PORT, type=int)
@click.option('--sample-format', type=click.Choice(object_readers('sample')), multiple=False, default=None, help=
'Select specific format of the sample')
@click.option('--scheme', type=click.Choice(available_schemes), multiple=False, default=None, help=
'Choose scheme to read the object from, defaulted to read from the FS.')
@click.option('-n', 'amount', type=int, default=-1, help=
'If mentioned, bounds the number of sent snapshots')
def upload_sample_cli(path, host, port, *, sample_format=None, scheme=None, amount=-1):
	"""
	Reads the sample from PATH and uploads it to the server listening on HOST:PORT.
	"""

	def publish_user(user):
		conn = Connection(f'http://{host}:{port}', user)
		return conn.upload

	publish_sample(path, sample_format=sample_format, scheme=scheme, publish_user=publish_user, amount=amount)


upload_sample = upload_sample_cli.callback


@log_error(logger)
def publish_sample(path, publish_user, *, sample_format=None, scheme=None, amount=-1):
	"""
	:param path: Where the sample is.
	:param publish_user: handles the publishing, the publisher would return a snapshot publisher to publish snapshots.
	:param sample_format: The format of the file which stores the sample (default=protobuf).
	:param scheme: Optional - The caller can request to fetch the file from place other than the FS.
	:param amount: If positive, bounds the amount of snapshots that would be uploaded.
	"""

	logger.info('Reading sample')
	logger.debug(f'Reading from {str(path)} by scheme {scheme}')
	user, snapshots = read_url(path, 'sample', version=sample_format, scheme=scheme)

	if amount > 0:
		snapshots = itertools.islice(snapshots, amount)
		logger.debug(f'Bounding amount of snpashots by {amount}')

	logging.info('Publishing user')
	publish_snapshot = publish_user(user)  # publishing function

	logger.info('Starting to upload snapshots...')
	counter = 0
	for snapshot in snapshots:
		counter += 1
		publish_snapshot(snapshot)

	logger.info(f'Total of {counter} snapshots had been uploaded')


if __name__ == '__main__':
	cli()
