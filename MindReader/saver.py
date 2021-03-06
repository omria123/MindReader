import logging
import os
import time

import click

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
		:param data: Dictionary of the form:
		{'user_id': ..., 'datetime': ..., name: {'result': ... , 'result_data': (URL/Path to binary file)}

		"""
		self.database.save(name, data)

	def save_user(self, user):
		"""
		Saves the user to the database.
		:param user: Dict representing the user's attrs
		"""
		self.database.save_user(user)


@click.group()
def cli():
	if 'WAITFORIT' in os.environ and os.environ['WAITFORIT'] == '1':
		time.sleep(10)


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
