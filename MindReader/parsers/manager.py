import importlib
import inspect
import functools

from pathlib import Path

INTERNAL_FILES = {'__init__.py', 'manager.py', '__main__.py'}
PARSERS = {}


def _collect_parsers():
	"""
	Collects parsers
	"""
	cur_dir = Path(__file__).parent
	possible_paths = filter(lambda path: str(path) not in INTERNAL_FILES, cur_dir.glob('*.py'))

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


def run_parser(parser_type, paths, publish, version=None):
	for path in paths:
		publish(parse(parser_type, path, version))


def parse(name, data, context=None):
	"""
	Parses the raw snapshot data given from the server.
	According to the given result_name, extract the appropriate part from the snapshot.
	:param name: The name of the parser which should be invoked.
	:param data: Raw snapshot data in bytes/str.
	:param context: Dependency injection object. Defaults to be NOP (which means it's just looking like everything is
	available)
	:return: The parsed value of the result_name from the raw snapshot
	"""
	if name not in PARSERS:
		raise ValueError('No such parser')
	data_parser = resolve_parser(name)
	# snapshot_dict = parse_snapshot(data, context)  # TODO define context
	data_parser(snapshot_dict)


def resolve_parser(name):
	"""
	Resolve the parser by given name, return it's wrapped version where every irrelevant argument is dropped.
	Nice to use when there are a lot of given kwargs which needs to be filtered
	:param name: Name of the required parser.
	:return:
	"""
	selected_parser = PARSERS[name]
	if not hasattr(selected_parser, 'fields'):
		# Add the fields manually. The [1:] slicing is required to skip the context positional
		selected_parser.fields = inspect.getfullargspec(selected_parser)[0][1:]

	@functools.wraps(selected_parser)
	def wrapper(context, *args, **kwargs):
		return selected_parser(context, *args,
		                       **{key: kwargs[key] for key in kwargs if key in selected_parser.fields})

	return wrapper


def parser(name=None):
	"""Collect a parser"""

	def decorator(f):
		args_spec = inspect.getfullargspec(f)
		f.fields = args_spec.args
		parser_name = name or (hasattr(f, 'name') and f.name)
		if parser_name:
			PARSERS[parser_name] = f
			return f
		raise ValueError('Parser has no name')

	return decorator
