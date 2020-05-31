import click
import logging

from . import Database, MessageQueue, IOAccess
from .utils import log_error

logger = logging.getLogger('Saver')


class Saver:
	"""
	The class is simply intended to get along with the requested API.
	The real functionality is in the general Database subpackage.
	"""

	def __init__(self, database, is_url=True):
		if is_url:
			self.database = Database.Database(database)
		else:
			self.database = database

	def save(self, name, data):
		"""
		Saves the published data to the DB.

		:param name: The name of the data being saved (i.e. the name of the appropriate parser)
		Note: This is useless and exists in the signature for future comparability and for the requirements of the API
		:param data: Dictionary of the form:
		{'user_id': ..., 'datetime': ..., name: {'result': ... , 'result_data': (URL/Path to binary file)}

		"""
		self.database.save(data)

	def save_user(self, user):
		"""
		Saves the user to the database.
		:param user: Dict representing the user's attrs
		"""
		self.database.save_user(user)


@click.group()
@click.option('--debug', is_flag=True)
@click.option('--no-logging', is_flag=True)
def cli(debug, no_logging):
	logging_level = logging.INFO
	if debug:
		logging_level = logging.DEBUG
	if no_logging:
		logging.disable()
	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging_level)


@cli.command('save')
@click.argument('result_name')
@click.argument('path')
@click.argument('database-url')
@log_error(logger)
def save(result_name, path, database_url):
	logger.info(f'Saving the result of the parser {result_name} from {path}')
	logger.debug(f'Saving to database {database_url}')
	data = IOAccess.read_url(path, 'json')
	Saver(database_url).save(result_name, data)


@cli.command('run-saver')
@click.argument('mq-url')
@click.argument('database-url')
@log_error(logger)
def run_saver(mq_url, database_url):
	"""
	Runs a parser which feeds from the message queue and save it to the db.
	"""
	logging.info('Running saver')
	saver = Saver(database_url)
	mq = MessageQueue.MessageQueue(mq_url)
	mq.run_saver(saver)


if __name__ == '__main__':
	cli()
