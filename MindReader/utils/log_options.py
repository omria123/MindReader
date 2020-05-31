import functools
import logging.config
from pathlib import Path


def log_error(logger, suppress=True):
	"""
	Reusable decorator which adds logging of possible exception raised to the function.
	Use as a safety-net rather then shortcut for logging.
	"""

	def decorator(f):
		@functools.wraps(f)
		def wrapper(*args, **kwargs):
			try:
				return f(*args, **kwargs)
			except Exception as e:
				logger.error(e)
				if not suppress:
					raise e

		return wrapper

	return decorator


config_path = str(Path(__file__).parent / 'log.ini')
logging.config.fileConfig(config_path)
