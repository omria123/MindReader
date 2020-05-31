import numpy as np
import matplotlib.pyplot as plt

DEFAULT_FORMAT = 'jpg'


def depth_image_parser(output, depth_image):
	"""
	Parse the image to matplotlib heatmap.
	"""

	height, width = depth_image.height, depth_image.width
	heat_map_values = np.array(depth_image.data).reshape(height, width)
	plt.imsave(output, heat_map_values, cmap='hot', format=DEFAULT_FORMAT)
	return {}


depth_image_parser.name = 'heatmap'
