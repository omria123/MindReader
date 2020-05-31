import logging

import click

from MindReader import IOAccess
from .utils import log_error
from .defaults import API_DEFAULT_HOST, API_DEFAULT_PORT

logger = logging.getLogger('CLI')


@click.group()
@click.option('-h', '--host', 'host', default=API_DEFAULT_HOST)
@click.option('-p', '--port', 'port', default=API_DEFAULT_PORT, type=int)
@click.pass_context
def cli(ctx, host, port):
	ctx.ensure_object(dict)
	ctx.obj['url_base'] = f'http://{host:{ctx.obj[port]}}'
	ctx.obj['publish'] = print


@cli.resultcallback
@click.pass_context
@log_error(logger)
def handle_result(ctx, result):
	ctx['publish'](result)


@cli.command()
@click.pass_context
@log_error(logger)
def get_users(ctx):
	"""Get basic details of all users"""
	logger.info('Getting users...')
	return IOAccess.read_url(f'{ctx["url_base"]}/users', 'json')


@cli.command()
@click.argument('user-id')
@click.pass_context
@log_error(logger)
def get_user(ctx, user_id):
	"""Get information on the user with USER-ID"""
	logger.info('Getting user...')
	logger.debug(f'{user_id=}')
	return IOAccess.read_url(f'{ctx["url_base"]}/users/{user_id}', 'json')


@cli.command()
@click.argument('user-id')
@click.pass_context
@log_error(logger)
def get_snapshots(ctx, user_id):
	"""Getting all the snapshots of user with USER-ID"""
	logger.info('Getting snapshots...')
	logger.debug(f'{user_id=}')
	return IOAccess.read_url(f'{ctx["url_base"]}/users/{user_id}/snapshots', 'json')


@cli.command()
@click.argument('user-id')
@click.argument('snapshot_id')
@click.pass_context
@log_error(logger)
def get_snapshot(ctx, user_id, snapshot_id):
	"""Get the description of snapshot with SNAPSHOT-ID of user with USER-ID"""
	logger.info('Getting snapshot...')
	logger.debug(f'{user_id=}, {snapshot_id=}')
	return IOAccess.read_url(f'{ctx["url_base"]}/users/{user_id}/snapshots/{snapshot_id}', 'json')


def save_result(path, result):
	with IOAccess.open(path) as fd:
		fd.write(result)


@cli.command()
@click.argument('user-id')
@click.argument('snapshot-id')
@click.argument('result-name')
@click.option('-s', '--save', 'path', help='If specified saving result to file')
@click.pass_context
@log_error(logger)
def get_result(ctx, user_id, snapshot_id, result_name, path):
	"""Get information of specific result of analysis on the snapshot with SNAPSHOT-ID of user with USER-ID"""
	logger.info('Getting result...')
	logger.debug(f'{user_id=}, {snapshot_id=}, {result_name=}')

	if path is not None:
		ctx.obj['publish'] = lambda result: save_result(path, result)
		logger.debug(f'Saving the result to {path}')

	return IOAccess.read_url(f'{ctx["url_base"]}/users/{user_id}/snapshots/{snapshot_id}/{result_name}', 'json')


if __name__ == '__main__':
	try:
		cli(obj={})
	except Exception as e:
		logger.error(e)
