"""
Abstraction of usage of databases.
To choose one, can either use DATABASES, or encode the message queue framework in the scheme.
Maintenance:
Simply add the implementation in a file in the subpackage.
Add the scheme as an attribute
"""

import importlib
from pathlib import Path

DATABASES = {}  # Scheme: Database-class

INTERNAL_FILES = {'__init__.py'}


def _collect_databases():
	"""
	Collects databases from subpackage
	"""
	cur_dir = Path(__file__).parent
	possible_paths = filter(lambda path: str(path.name) not in INTERNAL_FILES, cur_dir.glob('*.py'))
	for db_path in possible_paths:
		db_module_path = '.' + str(db_path.with_suffix('').relative_to(cur_dir)).replace('/', '.')
		db_module = importlib.import_module(db_module_path, package=__package__)
		for attr in dir(db_module):
			if attr.startswith('_') or not hasattr(attr, 'scheme'):
				continue
			try:
				database(getattr(db_module, attr))
			except ValueError:
				continue


def database(scheme=None):
	"""
	Collects databases interfaces.
	"""

	def decorator(obj):
		global scheme
		scheme = scheme or (hasattr(obj, 'scheme') and obj.scheme)
		if scheme:
			DATABASES[scheme] = obj
			return DATABASES
		raise ValueError('No scheme was mentioned')

	return decorator


_collect_databases()


class Database:
	"""
	General database which resolves the required scheme and select an
	appropriate database which can handle the communication.
	"""
	DEFAULT_SCHEME = 'mongo'

	def __init__(self, url, *args, **kwargs):
		self.url = url
		scheme = self.DEFAULT_SCHEME
		if '://' in url:
			scheme, url = url.split('://')

		if ':' in url:
			host, port = url.split(':')
		else:
			host, port = url, None

		self.database = DATABASES[scheme](host, port, *args, **kwargs)

	def __getattr__(self, item):
		return getattr(self.database, item)
