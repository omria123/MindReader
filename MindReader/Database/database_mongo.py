import json

import pymongo

import logging

logger = logging.getLogger('Database')


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
		client = pymongo.MongoClient(host, int(port), connect=False)
		db = client.db
		self.client = client
		self.db = db
		logger.info(f'Connected to DB {host}:{port}')

	def save(self, name, data):
		"""
		:param data: A dict which must have the following structure:
		{'user_id': ..., 'timestamp': ..., result_name: {'result': ..., 'result_data': (Optional - URL/Path to the file)}}.
		"""
		logger.info(f'Got new message to save - from {name}')
		snapshots = self.db.snapshots
		# Assuming to be one to one the identification to be 1-to-1.
		snapshot_identification = {
			'user_id': data['user_id'],
			'timestamp': data['timestamp'],
			'snapshot_id': data['snapshot_id']}

		snapshot = snapshots.find_one(snapshot_identification)
		if snapshot is None:
			logger.debug('Inserting new snapshot...')
			snapshots.insert_one(data)
			return

		result_dict = snapshot['result']
		result_dict[name] = data

		snapshots.update_one(snapshot_identification, {'$set': {'result': json.dumps(result_dict)}})
		logger.debug('Snapshot have been updated')

	def save_user(self, user: dict):
		"""
		Saves user to database
		:param user: User dictionary which holds the attribute of the user.
		"""
		logger.debug('Inserting new user....')
		users = self.db.users
		users.insert_one(user)
		logger.debug('New user inserted')

	def get_users(self):
		return [(user['username'], user['user_id']) for user in self.db.users.find({})]

	def get_user(self, user_id):
		user = self.db.users.find_one({'user_id': str(user_id)})
		if user is None:
			return None
		del user['_id']
		return user

	def get_snapshots(self, user_id):
		user = self.get_user(user_id)
		user_snapshots = self.db.snapshots.find({'user_id': user_id})

		def extract_basic_info(snapshot):
			return {
				'datetime': snapshot['datetime'],
				'user_id': snapshot['user_id'],
				'snapshot_id': snapshot['snapshot_id']}

		return user, list(map(extract_basic_info, map(self.fix_snapshot_result, user_snapshots)))

	def get_snapshot(self, user_id, snapshot_id):
		user = self.get_user(user_id)
		if user is None:
			return None, None
		snapshot = self.db.snapshots.find_one({'user_id': user_id, 'snapshot_id': snapshot_id})
		if snapshot is None:
			return user, None

		def extract_metadata(full_snapshot):
			return {
				'datetime': full_snapshot['datetime'],
				'user_id': full_snapshot['user_id'],
				'snapshot_id': full_snapshot['snapshot_id'],
				'results': list(full_snapshot['result'].keys()),
			}

		return user, extract_metadata(self.fix_snapshot_result(snapshot))

	def get_snapshot_result(self, user_id, snapshot_id, result_name):
		user, snapshot = self.get_snapshot(user_id, snapshot_id)
		if snapshot is None or user is None:
			return user, snapshot, None
		return user, snapshot, snapshot['result']['snapshot']

	@staticmethod
	def fix_snapshot_result(snapshot):
		snapshot['result'] = json.loads(snapshot['result'])
		return snapshot
