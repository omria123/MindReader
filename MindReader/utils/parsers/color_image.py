from PIL import Image


def color_image_parser(color_image):
	return


def color_image_to_pil(color_image):
	"""
	Loads the color_image from the snapshot object to an Image object from PIL
	:param color_image: image with height, width, and the data of the image.\
	:return: PIL.Image parsed version of color_image
	"""
	size = (color_image.width, color_image.height)
	image = Image.new('RGB', size)
	image.putdata(color_image.data)
	return image
