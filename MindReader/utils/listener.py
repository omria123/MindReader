import select
import socket

from .connection import Connection
from .session import Session


class Listener:
	BACKLOG = 100

	def __init__(self, addr):
		self._sock = self.create_socket_server(addr)
		self._connections = dict()

	def get_snapshots(self):
		while True:
			jobs, _, _ = select.select([self._sock] + self._connections.keys(), [], [])
			for job in jobs:
				if job is self._sock:
					self.receive_connection(job)
				else:
					response = self.handle_session(self._connections[job])
					if response is not None:
						yield response

	def handle_session(self, session):
		response, status = session.proceed()
		if status == session.STOP:
			self.close_session(session)
			return
		if status == session.SNAPSHOT:
			return session.user, response

	def receive_connection(self, sock):
		client, _ = sock.accept()
		self._connections[sock] = Session.server(Connection(sock))

	def close(self):
		for conn in self._connections:
			conn.close()
		self._sock.close()

	@classmethod
	def create_socket_server(cls, addr):
		s = socket.socket()
		s.bind(addr)
		s.listen(cls.BACKLOG)
		return s

	def close_session(self, session):
		session.close()
		self._connections.pop(session.connection._sock)
