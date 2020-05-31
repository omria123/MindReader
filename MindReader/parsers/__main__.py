'''import logging

import click

from . import parse, FORAMTS  # TODO: reformat


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


@cli.command(name='run-parser')
@cli.argument('name', help=f'Choose which parser you would like to run. (From {FORMATS})')
@cli.argument('mq', help='Message Queue which should by fed')
def run_parser(field, mq):
	pass


def parse(field, path):
	pass
'''

from pathlib import Path

import click

from .. import IOAccess


@click.group()
def cli():
	pass


def parse(result_name, snapshot_path):
	version = Path(snapshot_path).suffix
	if version not in IOAccess.object_readers('snapshot'):
		print('The snapshot encoding is not supported')
	IOAccess.read_url(snapshot_path, )
