import os
import csv
import sqlite3
import datetime
from .common import *

class WmtSession:
	def __init__(self, name, start, duration = None):
		self.name = name
		self.start = start
		self.duration = duration

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

	# if no id given, edit the last session
	# def setend(self, end, id = None):
	# 	with self.conn:
	# 		if (id == None):
	# 			self.conn.execute('''UPDATE sessions SET end = ? WHERE id = (SELECT MAX(id) FROM sessions)''', [end])
	# 		else:
	# 			self.conn.execute('''UPDATE sessions SET end = ? WHERE id = ?''', [end, id])
	# 	# maybe there's a way to update and return updated row in one statement?
	# 	return self.getsession(id)

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

	def print(self, n = 10):
		c = self.conn.execute('''SELECT * FROM
					(SELECT * FROM sessions ORDER BY start DESC LIMIT ?)
					ORDER BY start ASC''',
					[n])
		rows = c.fetchall()
		for row in rows:
			for record in range(len(row)):
				print(row[record], end=" ")
			print()

	def save(self):
		# TODO: call commit() here instead of calling using with self.conn:
		pass

	def export(self, filepath):
		import csv
		with  open(filepath, 'w') as f:
			writer = csv.DictWriter(f, fieldnames = ['name', 'start', 'duration'])
			writer.writeheader()
			c = self.conn.execute('''SELECT * FROM sessions''')
			rows = c.fetchall()
			for row in rows:
				r = {}
				r['name'] = str(row['name'])
				r['start'] = str(row['start'])
				r['duration'] = str(row['duration'])
				writer.writerow(r)
