import os
import csv
import sqlite3
import datetime
from .common import *

class WmtSession:
	def __init__(self, name, start, duration = None, id = None, end = None):
		self.name = name
		self.start = start
		self.id = id
		self.duration = duration
		if end is not None:
			self.setend(end)

	def setend(self, endtime):
		self.duration = int(round((endtime - self.start).total_seconds() / 60.0))

	def __str__(self):
		r = self.name + ' ' + str(self.start) + ' '
		if self.duration is None:
			r += '(' + str(round((datetime.datetime.now() - self.start).total_seconds() / 60.0)) + ' minutes)'
		else:
			r += str(self.duration) + ' minutes'
		return r

class Db:
	def __init__(self, localpath):
		self.localpath = localpath
		# PARSE_DECLTYPES is for parsing datetime in and out the db
		self.conn = sqlite3.connect(self.localpath, detect_types=sqlite3.PARSE_DECLTYPES)
		# Support dictionary cursor
		self.conn.row_factory = sqlite3.Row

		self.conn.execute('''
		CREATE TABLE IF NOT EXISTS sessions(
			id integer PRIMARY KEY,
			name text NOT NULL,
			start timestamp NOT NULL,
			duration integer)''')

	def insertsession(self, session):
		with self.conn:
			c = self.conn.execute('''
			INSERT INTO sessions (name, start, duration)
			VALUES (?, ?, ?)''',
			[session.name, session.start, session.duration])
			session.id = c.lastrowid

	def setsession(self, session):
		with self.conn:
			self.conn.execute('''UPDATE sessions SET
				name = ?, start = ?, duration = ?
				WHERE id = ?''',
				[session.name, session.start, session.duration, session.id])

	def _getsession(self, raw):
		return WmtSession(raw['name'], raw['start'], raw['duration'], raw['id'])

	def getsession(self, id = None):
		if (id == None):
			c = self.conn.execute('''SELECT * FROM sessions WHERE id = (SELECT MAX(id) FROM sessions)''')
		else:
			c = self.conn.execute('''SELECT * FROM sessions WHERE id = ?''', [id])

		return self._getsession(c.fetchone())

	def dropsession(self, id = None):
		with self.conn:
			if (id == None):
				self.conn.execute('''DELETE FROM sessions WHERE id = (SELECT MAX(id) FROM sessions)''')
			else:
				self.conn.execute('''DELETE FROM sessions WHERE id = ?''', [id])

	def _printsessions(self, conn):
		row_format ="{:<4} {:<25} {:<20} {:<6}"
		print(row_format.format(*[col[0] for col in conn.description]))
		for row in conn.fetchall():
			print(row_format.format(*[str(cell) for cell in row]))

	def printlastsessions(self, n = 10):
		c = self.conn.execute('''SELECT * FROM
					(SELECT * FROM sessions ORDER BY start DESC LIMIT ?)
					ORDER BY start ASC''',
					[n])
		self._printsessions(c)

	def _getsessions(self, conn):
		return [self._getsession(row) for row in conn]

	def getsessions(self, query):
		# TODO: return iterable of sessions according to given query
		pass

	def is_lastsession_running(self):
		return self.getsession().duration == None

	def save(self):
		# TODO: call commit() here instead of calling using with self.conn:
		pass

	def exportcsv(self, filepath):
		import csv
		with  open(filepath, 'w') as f:
			c = self.conn.execute('''SELECT * FROM sessions''')
			writer = csv.writer(f)
			writer.writerow([col[0] for col in c.description])
			for row in c.fetchall():
				writer.writerow(row)

	def importcsv(self, filepath):
		import csv
		with open(filepath, 'r') as f:
			reader = csv.DictReader(f)
			for row in reader:
				self.insertsession(WmtSession(row['name'], parsetime(row['start']), int(row['duration'])))
