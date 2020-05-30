"""
This subpackage abstract all the concepts of IO accesses, and all way of reading/writing objects from different resources.
The subpackage support 3 main features:
Drivers - Abstracts the concept of resource using the classical open API. Each driver must be a file-like object
Readers - Used to read objects from general locations.
Writers - Used to write objects to general locations.
"""
from .manager import WRITERS, READERS, DRIVERS, WRITERS_MIME_TYPE, READERS_MIME_TYPE
from .manager import driver, writer, reader, open, read, write, read_url, write_url, object_readers, object_writers
from . import Drivers, Readers, Writers
