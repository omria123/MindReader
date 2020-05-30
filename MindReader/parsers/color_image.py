from PIL import Image

FORMAT = 'jpeg'


def color_image_parser(output, color_image):
	"""
	Parse the image to BMP image.
	The image bytes are stored in different file which is file is given.
	"""
	shape = color_image.height, color_image.width
	image = Image.new('RGB', shape)
	image.putdata(color_image.data)
	image.save(output, format=FORMAT)
	return {'Content-Type': ''}


def color_image_to_pil(color_image):
	"""
	Loads the color_image from the snapshot object to an Image object from PIL
	:param color_image: Image with height, width, and the data of the image. Given as dict.
	:return: PIL.Image parsed version of color_image
	"""
	size = (color_image['width'], color_image['height'])
	image = Image.new('RGB', size)
	image.putdata(color_image['data'])

	return image


def extract_color_image_data(context, color_image):
	context.save(context.directory / 'color_image.raw', color_image['data'])
	return str(context.directory / 'color_image.binary')


color_image_parser.fields = ['color_image']
color_image_parser.name = 'color_image'
color_image_parser.hook = extract_color_image_data
