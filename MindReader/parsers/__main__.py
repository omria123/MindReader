import os
import time

import click

from .manager import PARSERS, parse, run_parsers, logger


available = list(PARSERS.keys())


@click.group()
def cli():
	if 'WAITFORIT' in os.environ and os.environ['WAITFORIT'] == '1':

		time.sleep(10)


@cli.command(name='run-parser')
@click.argument('mq-url')
@click.option('-n', '--name', 'parsers', multiple=True)
def run_parser(mq_url, parsers):
	f"""
	Run a parser for names (from {available}), to work with message queue at MQ-URL.
	If no NAME was mentioned all of them will be used (As one instance).
	"""
	logger.info(f'Running parsers for {parsers}')

	if len(parsers) == 0:
		parsers = available
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


if __name__ == '__main__':
	cli()
