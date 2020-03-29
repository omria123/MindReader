import socket
import struct


class Connection:
	MSG_HEADER_FMT = '<I'

	def __init__(self, addr):
		self._sock = addr
		if type(addr) is not socket.socket:
			self._sock = self.create_client_socket(addr)

	def __repr__(self):
		dst_ip, dst_port = self._sock.getpeername()
		src_ip, src_port = self._sock.getsockname()
		name = self.__class__.__name__
		return f'<{name} from {src_ip}:{src_port} to {dst_ip}:{dst_port}>'

	def write(self, data):
		if type(data) is str:
			data = bytes(data, 'utf-8')
		self._sock.sendall(data)

	def read(self, size):
		data = b''
		while len(data) < size:
			chunk = self._sock.recv(size - len(data))
			if len(chunk) == 0:
				raise ConnectionError
			data += chunk
		return data

	def close(self):
		self._sock.close()

	def send_message(self, message):
		message = struct.pack(self.MSG_HEADER_FMT, len(message)) + message
		self._sock.sendall(message)

	def receive_message(self):
		message_len_bin = self._sock.recv(struct.calcsize(self.MSG_HEADER_FMT))
		message_len, = struct.unpack(self.MSG_HEADER_FMT, message_len_bin)
		return self._sock.recv(message_len)

	def to_file(self, mode='r'):
		if mode == '':
			return self._sock.makefile(), self._sock.makefile(mode='w')
		return self._sock.makefile(mode='r')

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self._sock.close()

	@classmethod
	def connect(cls, addr, port):
		s = socket.socket()
		s.connect((addr, port))
		return cls(s)

	@staticmethod
	def create_client_socket(addr):
		s = socket.socket()
		s.connect(addr)
		return s
