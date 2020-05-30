"""
Generic protobuf helper functions.
"""


def object_to_protobuf(obj, protobuf_obj):
	"""
	:param obj: Object which holds fields for the protobuf_obj
	:param protobuf_obj: Object to transfer values to the protobuf
	"""
	if isinstance(obj, type(protobuf_obj)):
		protobuf_obj.MergeFrom(obj)  # The easy way
		return
	for field in protobuf_obj.DESCRIPTOR.fields_by_name:
		try:
			field_data = getattr(obj, field)
			target_field = getattr(obj, field)
			if hasattr(target_field, 'MergeFrom'):
				object_to_protobuf(field_data, target_field)
		except AttributeError:
			continue
