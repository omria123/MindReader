"""
Abstraction of usage of message queue.
To choose one, can either use MESSAGE_QUEUES, or encode the message queue framework in the scheme.
Maintenance:
Simply add the implementation in a file in the subpackage.
Add the scheme as an attribute
"""

import importlib
from pathlib import Path

MESSAGE_QUEUES = {}  # Scheme: Database-class

INTERNAL_FILES = {'__init__.py'}


def _collect_message_queues():
	"""
	Collects message queues from subpackage.
	"""
	cur_dir = Path(__file__).parent
	possible_paths = filter(lambda path: str(path.name) not in INTERNAL_FILES, cur_dir.glob('*.py'))

	for mq_path in possible_paths:
		mq_module_path = '.' + str(mq_path.relative_to(cur_dir).with_suffix('')).replace('/', '.')
		mq_module = importlib.import_module(mq_module_path, package=__package__)

		for attr in dir(mq_module):
			obj = getattr(mq_module, attr)
			if attr.startswith('_') or not hasattr(obj, 'scheme'):
				continue
			try:
				message_queue()(obj)
			except ValueError:
				continue


def message_queue(mq_scheme=None):
	"""
	Collect a message queue interface.
	"""

	def decorator(obj):
		nonlocal mq_scheme
		mq_scheme = mq_scheme or (hasattr(obj, 'scheme') and obj.scheme)
		if mq_scheme:
			MESSAGE_QUEUES[mq_scheme] = obj
			return MESSAGE_QUEUES
		raise ValueError('No scheme was mentioned')

	return decorator


class MessageQueue:
	DEFAULT_SCHEME = 'rabbitmq'

	def __init__(self, url, *args, **kwargs):
		self.url = url

		scheme = self.DEFAULT_SCHEME

		if '://' in url:
			scheme, url = url.split('://', 1)

		if ':' in url:
			host, port = url.split(':')
		else:
			host, port = url, None

		self.mq = MESSAGE_QUEUES[scheme](host, port, *args, **kwargs)

	def __getattr__(self, item):
		return getattr(self.mq, item)


_collect_message_queues()
