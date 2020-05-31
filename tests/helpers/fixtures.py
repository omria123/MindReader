import time
from multiprocessing import Process
import random
from subprocess import Popen, DEVNULL, call as subprocess_call

import pytest

from MindReader.utils.protobuf.cortex_pb2 import User, Snapshot, ColorImage, DepthImage, Feelings, Pose
from MindReader import MessageQueue, Database, Saver
from MindReader.parsers import PARSERS
from MindReader.server import cli_run_server
from MindReader import run_server, run_api_server, IOAccess, run_parser

TEST_DATABASE_PORT = 7070
TEST_DATABASE_ADDR = f'mongo://127.0.0.1:{TEST_DATABASE_PORT}'
TEST_MQ_PORT = 9090
TEST_MQ_ADDR = f'rabbitmq://localhost:{TEST_MQ_PORT}'
TEST_API_PORT = 6060
TEST_SERVER_PORT = 5050


###########################
# INIT ENTITIES
###########################

@pytest.fixture
def all_workers(parsers, saver):
	def run(mq, db, is_url=True, consume=True):
		if is_url:
			mq = MessageQueue.MessageQueue(mq)
			db = Database.Database(db)
		parsers(mq, False, False)
		saver(mq, db, False, False)
		if consume:
			mq.consume()

	return run


@pytest.fixture
def parsers():
	def run(mq, is_url=True, consume=True):
		if is_url:
			mq = MessageQueue.MessageQueue(mq)

		for name in PARSERS:
			mq.run_parser(PARSERS[name], start_consuming=False)

		if consume:
			mq.consume()

	return run


@pytest.fixture()
def saver():
	def run(mq, db, is_url=True, consume=True):
		if is_url:
			mq = MessageQueue.MessageQueue(mq)
		mq.run_saver(Saver(db, is_url), consume)
		if consume:
			mq.consume()

	return run


@pytest.fixture
def cli_server(tmp_path):
	def start(mq_url):
		cli_run_server.callback(mq_url, start.host, start.port, str(tmp_path))

	start.host, start.port = '127.0.0.1', TEST_SERVER_PORT
	return start


@pytest.fixture
def server():
	def start(publish_user, publish_snapshot):
		args = (start.host, start.port, publish_user, publish_snapshot)
		run_server(*args)

	start.host, start.port = '127.0.0.1', TEST_SERVER_PORT
	return start


@pytest.fixture
def mq(request):
	def finalizer():
		subprocess_call(['docker', 'stop', 'test-mq'], stdout=DEVNULL)
		subprocess_call(['docker', 'rm', 'test-mq'], stdout=DEVNULL)

	request.addfinalizer(finalizer)
	Popen(['docker', 'run', '--name', 'test-mq', '-d', '-p', f'{TEST_MQ_PORT}:5672', 'rabbitmq'], stdout=DEVNULL)

	def get():
		return MessageQueue.MessageQueue(TEST_MQ_ADDR)

	time.sleep(11)  # Take time to make sure the docker is up
	get.url = TEST_MQ_ADDR
	return get


@pytest.fixture
def db(request):
	def finalizer():
		subprocess_call(['docker', 'stop', 'test-db'], stdout=DEVNULL)
		subprocess_call(['docker', 'rm', 'test-db'], stdout=DEVNULL)

	request.addfinalizer(finalizer)
	Popen(['docker', 'run', '--name', 'test-db', '-d', '-p', f'{TEST_DATABASE_PORT}:27017', 'mongo'], stdout=DEVNULL)

	def get():
		return Database.Database(TEST_DATABASE_ADDR)

	time.sleep(11)  # Take time to make sure the docker is up
	get.url = TEST_DATABASE_ADDR
	return get


@pytest.fixture
def api_server(db):
	Process(target=run_api_server, args=()).start()
	time.sleep(1)


###########################
# FAKE (NOT NEWS)
###########################


class MockResponse:
	def __init__(self, status_code, result):
		self.status_code = status_code
		self.result = result

	def json(self):
		return self.result


class RequestCapture:
	pass


@pytest.fixture
def fake_http_writing(monkeypatch):
	old_write_url = IOAccess.write_url
	request = RequestCapture()

	def mock_write_url(url, name, obj, *args, headers=None, version=None, **kwargs):
		if not isinstance(url, str) or not url.startswith('http://'):  # Fix only HTTP access
			return old_write_url(url, name, obj, *args, headers=headers, version=version, **kwargs)
		request.url = url
		request.headers = headers
		request.obj = obj
		return MockResponse(200, ['username', 'user_id', 'gender', 'birthday'])

	monkeypatch.setattr(IOAccess, 'write_url', mock_write_url)
	return request


##########################
# PROTOBUF DATA FACTORIES
##########################
# Dependencies:
# Sample -> User, Snapshot
# User, Snapshot -> Date.
# Snapshot -> Pose, Feelings, ColorImage, DepthImage
# Pose -> Translation, Rotation

def rand_float(a, b):
	return random.random() * (b - a) + a


@pytest.fixture
def date_factory():
	def rand_date():
		return int(time.time() + 15000 * (random.random() - 1))

	return rand_date


@pytest.fixture
def user_factory(date_factory):
	names = ['Alice', 'Bob', 'Connor', 'Dana']

	def new(max_id=100):
		new_user = User()
		new_user.birthday = date_factory()
		new_user.gender = random.randint(0, 2)
		new_user.user_id = random.randint(0, max_id)
		new_user.username = random.choice(names)
		return new_user

	return new


@pytest.fixture
def translation_factory():
	def new():
		new_translation = Pose.Translation()
		for field in new_translation.DESCRIPTOR.fields_by_name:
			setattr(new_translation, field, rand_float(-50, 50))
		return new_translation

	return new


@pytest.fixture
def rotation_factory():
	def new():
		new_rotation = Pose.Rotation()
		for field in new_rotation.DESCRIPTOR.fields_by_name:
			setattr(new_rotation, field, rand_float(-50, 50))
		return new_rotation

	return new


@pytest.fixture
def feelings_factory():
	def new():
		feelings = Feelings()
		for field in Feelings.DESCRIPTOR.fields_by_name:
			setattr(feelings, field, rand_float(-1, 1))
		return feelings

	return new


@pytest.fixture
def pose_factory(translation_factory, rotation_factory):
	def new():
		new_pose = Pose()
		new_pose.translation.MergeFrom(translation_factory())
		new_pose.rotation.MergeFrom(rotation_factory())
		return new_pose

	return new


@pytest.fixture
def color_image_factory():
	def new(height, width):
		new_image = ColorImage()
		new_image.height, new_image.width = height, width

		rgb_values = [random.randint(0, 255) for _ in range(3 * height * width)]
		new_image.data = bytes(rgb_values)
		return new_image

	return new


@pytest.fixture
def depth_image_factory():
	def new_depth_image(height, width, max_distance=20):
		new_image = DepthImage()
		new_image.height, new_image.width = height, width
		new_image.data.extend([max_distance * random.random() for _ in range(height * width)])
		return new_image

	return new_depth_image


@pytest.fixture
def snapshot_factory(date_factory, pose_factory, color_image_factory, depth_image_factory,
                     feelings_factory):
	def new():
		snapshot = Snapshot()
		snapshot.datetime = date_factory()
		snapshot.pose.MergeFrom(pose_factory())
		snapshot.color_image.MergeFrom(color_image_factory(15, 15))

		snapshot.depth_image.MergeFrom(depth_image_factory(15, 15))
		snapshot.feelings.MergeFrom(feelings_factory())
		return snapshot

	return new


@pytest.fixture
def sample_factory(user_factory, snapshot_factory):
	def new(amount=10):
		def snapshots_iter():
			for _ in range(amount):
				yield snapshot_factory()

		return user_factory(), snapshots_iter()

	return new
