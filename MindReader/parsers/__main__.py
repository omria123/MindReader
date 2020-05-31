import click
from .manager import PARSERS, parse, run_parsers

available = list(PARSERS.keys())


@click.group()
def cli():
	pass


@cli.command(name='run-parser')
@click.argument('mq-url')
@click.option('-n', '--name', 'parsers', multiple=True)
def run_parser(mq_url, parsers):
	f"""
	Run a parser for NAME (from {available}), to work with message queue at MQ-URL.
	"""
	if len(parsers) == 0:
		print('No parser was given!')
		return
	run_parsers(mq_url, parsers)


@cli.command(name='parse')
@click.argument('path')
@click.argument('name')
def cli_parse(path, name):
	f"""
	Parse a snapshot from PATH according to NAME (From {available}). Prints the result to stdout.
	Note: The PATH suffix represents the snapshot encoding.
	"""
	print(parse(name, path))
