def pose_parser(pose):
	return {'translation': parse_translation(pose.translation),
	        'rotation': parse_rotation(pose.rotation)}


def parse_translation(translation):
	attrs = ['x', 'y', 'z']
	return {attr: getattr(translation, attr) for attr in attrs}


def parse_rotation(rotation):
	attrs = ['x', 'y', 'z', 'w']
	return {attr: getattr(rotation, attr) for attr in attrs}


pose_parser.name = 'pose'
