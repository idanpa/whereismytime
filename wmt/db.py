import os
import csv
import sqlite3
import datetime
from .common import *

class WmtSession:
	def __init__(self, name, start, end = None):
		self.start = start
		self.end = end
		self.name = name

		if end is None:
			self.duration = (datetime.datetime.now() - start).total_seconds() / 60
		else:
			self.duration = int((end - start).total_seconds() / 60)

class Db:
	def __init__(self, localpath):
		self.localpath = localpath
		self.conn = sqlite3.connect(self.localpath, detect_types=sqlite3.PARSE_DECLTYPES)

		self.conn.execute('''
		CREATE TABLE IF NOT EXISTS sessions(
			id integer PRIMARY KEY,
			name text NOT NULL,
			start timestamp NOT NULL,
			end timestamp)''')

	def insertsession(self, session):
		with self.conn:
			c = self.conn.execute('''
			INSERT INTO sessions (start, end, name)
			VALUES (?, ?, ?)''',
			[session.start, session.end, session.name])
			return c.lastrowid

	# if no id given, edit the last session
	def setend(self, end, id = None):
		with self.conn:
			if (id == None):
				self.conn.execute('''UPDATE sessions SET end = ? WHERE id = (SELECT MAX(id) FROM sessions)''', [end])
			else:
				self.conn.execute('''UPDATE sessions SET end = ? WHERE id = ?''', [end, id])
		# maybe there's a way to update and return updated row in one statement?
		return self.getsession(id)


	def setsession(self, session, id = None):
		with self.conn:
			if (id == None):
				self.conn.execute('''UPDATE sessions SET
					start = ?, end = ?, name = ?
					WHERE id = (SELECT MAX(id) FROM sessions)''',
					[session.start, session.end, session.name])
			else:
				self.conn.execute('''UPDATE sessions SET
					start = ?, end = ?, name = ?
					WHERE id = ?''',
					[session.start, session.end, session.name,
					id])

	def getsession(self, id = None):
		if (id == None):
			c = self.conn.execute('''SELECT name, start, end FROM sessions WHERE id = (SELECT MAX(id) FROM sessions)''')
		else:
			c = self.conn.execute('''SELECT name, start, end FROM sessions WHERE id = ?''', [id])

		raw = c.fetchone()
		return WmtSession(raw[0], raw[1], raw[2])

	def print(self, n = 10):
		c = self.conn.execute('''SELECT * FROM sessions''')
		rows = c.fetchall()
		for row in rows:
			for record in range(len(row)):
				print(row[record], end=" ")
			print()

	def save(self):
		# TODO: call commit() here instead of calling using with self.conn:
		pass

