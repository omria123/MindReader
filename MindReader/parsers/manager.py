import importlib
import inspect
import logging

from pathlib import Path

from .. import IOAccess, MessageQueue

logger = logging.getLogger('parsers')

INTERNAL_FILES = {'__init__.py', 'manager.py', '__main__.py'}
PARSERS = {}


def _collect_parsers():
	"""
	Collects parsers
	"""
	cur_dir = Path(__file__).parent
	possible_paths = filter(lambda path: str(path.name) not in INTERNAL_FILES, cur_dir.glob('*.py'))

	for parser_path in possible_paths:
		parser_module_path = '.' + str(parser_path.with_suffix('').relative_to(cur_dir)).replace('/', '.')
		parser_module = importlib.import_module(parser_module_path, package=__package__)

		for attr in dir(parser_module):
			if attr.startswith('_'):
				continue  # Ignore private

			if not hasattr(getattr(parser_module, attr), 'name') or not attr.endswith('parser'):
				continue  # Identified as parser

			if hasattr(attr, 'fields'):
				continue  # Already collected

			try:
				parser()(getattr(parser_module, attr))
			except ValueError:
				continue


def parser(name=None):
	"""Collects a parser"""

	def decorator(f):
		args_spec = inspect.getfullargspec(f)
		f.fields = args_spec.args
		parser_name = name or (hasattr(f, 'name') and f.name)
		if parser_name:
			PARSERS[parser_name] = f
			return f
		raise ValueError('Parser has no name')

	return decorator


def parse(snapshot_path, result_name):
	"""Parses a message"""
	snapshot_path = Path(snapshot_path)
	version = snapshot_path.suffix[1:]

	if version not in IOAccess.object_readers('snapshot'):
		logger.error('The snapshot encoding is not supported')
		return
	if result_name not in PARSERS:
		logger.error('Bad result name: no such parser')
		return

	selected_parser = PARSERS[result_name]
	fields = selected_parser.fields
	logger.info(f'Parser {result_name} got new work')
	logger.debug(f'The requested snapshot is at: {snapshot_path}')

	with IOAccess.open(str(snapshot_path), mode='rb') as fd:
		snapshot = IOAccess.read(fd, 'snapshot', version=version)

	output_path = str(snapshot_path.parent / f'{result_name}.binary')

	try:
		args = {field: getattr(snapshot, field) for field in fields if field != 'output'}
	except AttributeError:
		logger.info("The snapshot doesn't have the value")
		return

	if 'output' in fields:
		logger.debug(f'The result data will be saved to {output_path}')
		args['output'] = IOAccess.open(output_path, 'wb')

	result = selected_parser(**args)

	logger.info('Parser finished')
	logger.debug(f'Parser returned {result}')

	published_result = {
		'result': {result_name: {'metadata': result}},
		'timestamp': snapshot.datetime,
	}
	if 'output' in args:
		published_result['result'][result_name]['location'] = output_path
		output = args['output']
		published_result['result'][result_name]['Content-Length'] = output.seek(0, 2)
		output.close()

	return published_result


def run_parsers(mq, parsers, is_url=True, start_consuming=True):
	"""
	Runs the parsers to the mq.
	If is_url is False then mq is assumed to be MessageQueue object.
	"""
	if is_url:
		mq = MessageQueue.MessageQueue(mq)

	for name in parsers:
		mq.run_parser(name, lambda path: parse(path, name), start_consuming=False)

	if start_consuming:
		mq.consume()
