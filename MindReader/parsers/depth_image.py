import mimetypes

import numpy as np
import matplotlib.pyplot as plt

FORMAT = 'jpg'


def depth_image_parser(output, depth_image):
	"""
	Parse the image to matplotlib heatmap.
	"""

	height, width = depth_image.height, depth_image.width
	heat_map_values = np.array(depth_image.data).reshape(height, width)
	plt.imsave(output, heat_map_values, cmap='hot', format=FORMAT)
	return {
		'Content-Type': mimetypes.types_map[f'.{FORMAT}'],
		'height': depth_image.height,
		'width': depth_image.width}


depth_image_parser.name = 'heatmap'
