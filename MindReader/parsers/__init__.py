"""
The subpackage offers different parsers.
They are all available with PARSERS.

Maintenance:
A parser must has the following properties:

1. Request every field it needs as argument and it will accept it as an object.
2. Specify name: parser.name = 'name', otherwise should be collected with the parser
decorator.
3. The parser function name must endswith parser
4. The parser must return the value as a jsonable value.
5. The parser can specify the special argument output, to write binary blob.
5.a. The parser should return in it's answer a dict {'Content-Type': ...}. This helps the API to expose a richer metadata
on the result.
Note: The fields has to be main fields of a snapshot.
"""

from .manager import parser, parse, PARSERS, run_parsers
from .manager import _collect_parsers

_collect_parsers()

