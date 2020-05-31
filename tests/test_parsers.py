import io

from PIL import Image
import pytest

from MindReader import parsers
from MindReader.parsers import color_image
from MindReader.utils.protobuf import ColorImage

RESULTS = {
	'heatmap': {'depth_image', 'output'},
	'color_image': {'color_image', 'output'},
	'feelings': {'feelings'},
	'pose': {'pose'}}

MAX_DIFF = 300  # Since some change still occur if images are the same


def test_parsers_fields():
	assert RESULTS == {name: set(parser.fields) for name, parser in parsers.PARSERS.items()}


def image_to_bytes(im, h, w):
	pixel_matrix = im.load()
	data = b''
	for i in range(w):
		for j in range(h):
			pixel = pixel_matrix[i, j]
			data += bytes(pixel)
	return data


# Images for this test must be in loseless format
@pytest.mark.parametrize('image_path,image_format', [
	('image.png', 'png'),
])
def test_color_image(image_path, image_format, tmp_path):
	color_image.FORMAT = image_format

	with open(image_path, 'rb') as fd:
		image_data = fd.read()

	ci = ColorImage()
	im = Image.open(image_path)
	width, height = im.size
	ci.height = height
	ci.width = width
	ci.data = image_to_bytes(im, height, width)

	with io.BytesIO() as output:
		parsers.PARSERS['color_image'](output, ci)
		with io.BytesIO() as compare:
			im.save(compare, format=image_format)
			assert abs(len(output.getvalue()) - len(image_data)) < 1000

# For the rest I don't have any interesting tests
