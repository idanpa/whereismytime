import os
import csv
import sqlite3
import datetime
from .common import *

class WmtSession:
	def __init__(self, name, start, duration = None, end = None):
		self.name = name
		self.start = start
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
			return c.lastrowid

	def setsession(self, session, id = None):
		with self.conn:
			if (id == None):
				self.conn.execute('''UPDATE sessions SET
					name = ?, start = ?, duration = ?
					WHERE id = (SELECT MAX(id) FROM sessions)''',
					[session.name, session.start, session.duration])
			else:
				self.conn.execute('''UPDATE sessions SET
					name = ?, start = ?, duration = ?
					WHERE id = ?''',
					[session.name, session.start, session.duration,
					id])

	def getsession(self, id = None):
		if (id == None):
			c = self.conn.execute('''SELECT * FROM sessions WHERE id = (SELECT MAX(id) FROM sessions)''')
		else:
			c = self.conn.execute('''SELECT * FROM sessions WHERE id = ?''', [id])

		raw = c.fetchone()
		return WmtSession(raw['name'], raw['start'], raw['duration'])

	def dropsession(self, id = None):
		with self.conn:
			if (id == None):
				self.conn.execute('''DELETE FROM sessions WHERE id = (SELECT MAX(id) FROM sessions)''')
			else:
				self.conn.execute('''DELETE FROM sessions WHERE id = ?''', [id])

	def printsessions(self, n = 10):
		row_format ="{:<4} {:<15} {:<20} {:<6}"
		c = self.conn.execute('''SELECT * FROM
					(SELECT * FROM sessions ORDER BY start DESC LIMIT ?)
					ORDER BY start ASC''',
					[n])
		print(row_format.format(*[col[0] for col in c.description]))
		rows = c.fetchall()
		for row in rows:
			print(row_format.format(*[str(cell) for cell in row]))

	def getsessions(self, query):
		# TODO: return iterable of sessions according to given query
		pass

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
