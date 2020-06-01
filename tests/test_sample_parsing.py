import itertools

from google.protobuf.json_format import ParseDict

from MindReader import IOAccess
from MindReader.utils.protobuf import User


def test_sample(sample_factory, tmp_path):
	user, snapshots = sample_factory()
	c, s = itertools.tee(snapshots)
	with open(str(tmp_path / 'sample'), 'wb') as fd:
		IOAccess.write(fd, 'sample', user, s)

	with open(str(tmp_path / 'sample'), 'rb') as fd:
		new_user_dict, new_s = IOAccess.read(fd, 'sample')
	new_user = User()
	assert ParseDict(new_user_dict, new_user).SerializeToString() == user.SerializeToString()
	for comp, source in zip(c, new_s):
		assert comp.SerializeToString() == source.SerializeToString()
