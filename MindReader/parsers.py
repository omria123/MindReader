def resolve_parser(parser_type, version):
	return lambda x: x


def parse(parser_type, path, version=None):
	with open(path, 'rb') as reader:
		parser = resolve_parser(parser_type, version)
		return parser(reader)


def run_parser(parser_type, paths, publish, version=None):
	for path in paths:
		publish(parse(parser_type, path, version))
