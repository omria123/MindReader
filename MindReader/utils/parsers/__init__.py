def parse(parser_type, path, version=None):
	with open(path, 'rb') as reader:
		return resolve_parser(parser_type, version)()


def run_parser(parser_type, paths, publish, version=None):
	for path in paths:
		publish(parse(parser_type, path, version))


def parser(name):
	pass
