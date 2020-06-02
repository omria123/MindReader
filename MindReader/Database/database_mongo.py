import functools
import json

import pymongo

import logging

logger = logging.getLogger('Database')


def string_ids(f):
	"""
	Wraps the function, so that the id's it gets will always be strings
	"""

	@functools.wraps(f)
	def wrapper(self, *args):
		return f(self, *[str(arg) for arg in args])

	return wrapper


class MongoDatabase:
	"""
	Mongodb implementation of the database.
	"""
	scheme = 'mongo'
	DEFAULT_PORT = 27017
	SUPPORTABLE_FIELDS = ['pose', 'color_image', 'depth_image', 'feelings']  # TODO: change this

	def __init__(self, host, port=None):
		if port is None:
			port = self.DEFAULT_PORT
		self.host, self.port = host, port
		try:

			client = pymongo.MongoClient(host, int(port), connect=False)
		except Exception as e:
			logger.error('Couldnt connect to DB')
			logger.error(e)
			raise e

		db = client.db
		self.client = client
		self.db = db
		db.users.create_index([('user_id', pymongo.ASCENDING)], unique=True)

		logger.info(f'Connected to DB {host}:{port}')

	def save(self, name: str, data: dict):
		"""
		:param data: A dict which must have the following structure:
		{'user_id': ..., 'timestamp': ..., result_name: {'result': ..., 'result_data': (Optional - URL/Path to the file)}}.
		"""
		logger.info(f'Got new message to save - from {name}')
		snapshots = self.db.snapshots
		iden = self.snapshot_identification(data)
		snapshot = snapshots.find_one(iden)
		if snapshot is None:
			logger.debug('Inserting new snapshot...')
			data['result'] = json.dumps(data['result'])
			snapshots.insert_one(data)
			return
		logger.info(str(data['result']))
		result_dict = json.loads(snapshot['result'])
		result_dict[name] = data['result'][name]

		snapshots.update_one(iden, {'$set': {'result': json.dumps(result_dict)}})
		logger.debug('Snapshot have been updated')

	def save_user(self, user: dict):
		"""
		Saves user to database
		:param user: User dictionary which holds the attribute of the user.
		"""
		logger.debug('Inserting new user....')
		users = self.db.users
		users.update(self.user_identification(user), user, upsert=True)
		logger.debug('New user inserted')

	def get_users(self):
		all_users = list(self.db.users.find({}))
		for user in all_users:
			del user['_id']
		return all_users

	@string_ids
	def get_user(self, user_id):
		user = self.db.users.find_one({'user_id': user_id})
		if user is None:
			return None
		del user['_id']
		return user

	@string_ids
	def get_snapshots(self, user_id):
		user_snapshots = self.db.snapshots.find({'user_id': user_id})
		if user_snapshots is None:
			return user_snapshots
		return list(map(self.fix_snapshot_result, user_snapshots))

	@string_ids
	def get_snapshot(self, user_id, snapshot_id):
		user = self.get_user(user_id)
		if user is None:
			return None, None
		snapshot = self.db.snapshots.find_one({'user_id': user_id, 'snapshot_id': snapshot_id})
		if snapshot is None:
			return user, None

		return user, self.fix_snapshot_result(snapshot)

	@string_ids
	def get_snapshot_result(self, user_id, snapshot_id, result_name):
		user, snapshot = self.get_snapshot(user_id, snapshot_id)
		if snapshot is None or user is None or result_name not in snapshot['result']:
			return user, snapshot, None
		return user, snapshot, snapshot['result'][result_name]

	@string_ids
	def get_snapshots_amount(self, user_id):
		return self.db.snapshots.count({'user_id': user_id})

	@staticmethod
	def fix_snapshot_result(snapshot):
		snapshot['result'] = json.loads(snapshot['result'])
		del snapshot['_id']
		return snapshot

	@staticmethod
	def snapshot_identification(snapshot):
		"""
		One to one identification of the snapshots.
		"""
		return {
			'user_id': snapshot['user_id'],
			'timestamp': snapshot['timestamp'],
			'snapshot_id': snapshot['snapshot_id']}

	@staticmethod
	def user_identification(user):
		return {'user_id': user['user_id']}

	def __str__(self):
		return f'{self.scheme}://{self.host}:{self.port}'

	def __repr__(self):
		return f'MongoDatabase({str(self)})'
