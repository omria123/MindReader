_encoders = {}
_decoders = {}


##################################################################
# EXPORTED API functions
##################################################################
def encode_snapshot(snapshot, fields, config):
	"""
	Encode a snapshot object in respect to given configuration and available fields
	:param snapshot: A snapshot object to encode
	:param fields: The available fields in the snapshot object
	:param config: A list of different encoding types which the snapshot can be encoded to. The first available will
	be used (gives a way of prioritizing different versions. As a simple use case, a simple string can be given
	if there is only one available format.
	:return encoded object, along with the chosen encoding
	"""
	if type(config) is not list:
		config = [config]

	for encoding_type in config:
		if encoding_type in _encoders:
			return _encoders[encoding_type](snapshot, fields), encoding_type

	raise NotImplemented('Encoding type has no implemented encoder')


def decode_snapshot(data, encoding_type):
	"""
	Decodes a snapshot according to given encoding type
	:param data: Raw data of encoded snapshot
	:param encoding_type: string representing the encoding of the snapshot
	:return: Snapshot object
	"""

	if encoding_type not in _decoders:
		raise NotImplemented('Encoding type has no implemented decoder')
	return _decoders[encoding_type](data)


##################################################################
# ENCODERS/DECODERS COLLECTORS
##################################################################
def encoder(encoding_type):
	"""
	Collect encoders for the Config class
	:param encoding_type: the encoding type which the function encodes
	:return: decorator to collect encoder of the given encoding type
	"""

	def decorator(f):
		_encoders[encoding_type] = encoding_type
		return f

	return decorator


def decoder(encoding_type):
	"""
	Collect decoders for the Config class
	:param encoding_type: the encoding type which the function decodes
	:return: decorator to collect decoder of the given encoding type
	"""

	def decorator(f):
		_decoders[encoding_type] = encoding_type
		return f

	return decorator


##################################################################
# ENCODERS AND DECODERS
##################################################################
class SnapshotDummy:
	pass


@encoder('protobuf_snapshot_v1')
def protobuf_snapshot_encoder(snapshot, fields=None):
	filtered_snapshot = SnapshotDummy()
	if fields is None:
		fields = []
	for field in fields:
		setattr(filtered_snapshot, field, getattr(snapshot, field))
	return


@decoder('protobuf_snapshot_v1')
def protobuf_snapshot_decoder():
	pass
