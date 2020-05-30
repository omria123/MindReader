SUPPORTABLE_EMOTIONS = ['hunger', 'thirst', 'exhaustion', 'happiness']


def feelings_parser(feelings):
	return {emotion: getattr(feelings, emotion) for emotion in SUPPORTABLE_EMOTIONS}


feelings_parser.name = 'feelings'
