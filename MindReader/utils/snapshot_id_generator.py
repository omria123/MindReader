"""
Generates IDs.
This is a nice abstraction, since the generator can be:
1. durable
2. work with few threads
3. work with few servers
Without changing the api, only by changing the next_snapshot_id function
"""

from pathlib import Path
import struct

from ..IOAccess import open

COUNTER_FILE = Path(__file__).parent / 'counter'


def durable_id_generator():
	counter = 0
	target_path = str(COUNTER_FILE)
	if not COUNTER_FILE.exists():
		with open(target_path, 'wb') as fd:
			fd.write(struct.pack('<L', counter))
		yield counter

	while True:
		with open(target_path, 'rb') as fd:
			counter, = struct.unpack('<L', fd.read(4))
		counter += 1
		with open(target_path, 'wb') as fd:
			fd.write(struct.pack('<L', counter))
		yield counter


next_snapshot_id = durable_id_generator().__next__
