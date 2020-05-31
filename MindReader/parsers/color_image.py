import mimetypes

from PIL import Image

FORMAT = 'jpeg'


def color_image_parser(output, color_image):
	"""
	Parse the image to BMP image.
	The image bytes are stored in different file which is file is given.
	"""
	shape = color_image.width, color_image.height
	image = Image.new('RGB', shape)
	image.frombytes(color_image.data)
	image.save(output, format=FORMAT)
	return {'Content-Type': mimetypes.types_map[f'.{FORMAT}']}


color_image_parser.name = 'color_image'
