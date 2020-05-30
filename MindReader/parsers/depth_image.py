import numpy as np
import struct

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

DEFAULT_LINE_WIDTH = 1
DEFAULT_DEPTH_IMAGE_FORMAT = 'png'


def depth_image_parser(output, depth_image):
	"""
	Parse the image to matplotlib heatmap.
	"""

	height, width = depth_image['height'], depth_image['width']
	heat_map_values = np.array(struct.unpack((height * width) * 'f', depth_image['data'])).reshape(height, width)
	sns.heatmap(pd.DataFrame(heat_map_values), linewidth=DEFAULT_LINE_WIDTH, cmap='coolwarm')
	plt.savefig(output, format='png')
	return {}


depth_image_parser.name = 'heatmap'
