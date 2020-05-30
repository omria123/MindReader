import functools
import logging.config
from pathlib import Path


def log_error(logger):
	"""
	Reusable function which adds logging of possible exception raised
	"""

	def decorator(f):
		@functools.wraps(f)
		def wrapper(*args, **kwargs):
			try:
				return f(*args, **kwargs)
			except Exception as e:
				logger.error(e)

		return wrapper

	return decorator


config_path = str(Path(__file__).parent / 'log.ini')
logging.config.fileConfig(config_path)
