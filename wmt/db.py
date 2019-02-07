import os
import sqlite3
import datetime
from .common import *
from itertools import groupby
from itertools import tee

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
			duration = round((datetime.datetime.now() - self.start).total_seconds() / 60.0)
			if duration > 0:
				r += '(' + str(duration) + ' minutes)'
		else:
			r += str(self.duration) + ' minutes'
		return r

def sumdurations(sessions):
	# sum all durations, if duration is empty, consider session as still running:
	return sum(s.duration if s.duration is not None else int(round((datetime.datetime.now() - s.start).total_seconds() / 60.0)) for s in sessions)

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

	def _printsessionstable(self, sessions):
		row_format ="{:<4} {:<25} {:<20} {:<6}"
		print(row_format.format('id', 'name', 'start', 'duration'))
		for s in sessions:
			if s.duration is None:
				dur = '(' + str(int(round((datetime.datetime.now() - s.start).total_seconds() / 60.0))) + ')'
			else:
				dur = str(s.duration)
			print(row_format.format(s.id, s.name, str(s.start), dur)) # TODO: add id to sessions?

	def reportlast(self, n = 10):
		ss = self._getsessions('''SELECT * FROM
					(SELECT * FROM sessions ORDER BY start DESC LIMIT ?)
					ORDER BY start ASC''',
					[n])
		self._printsessionstable(ss)

	def _reportday(self, sessions, level):
		if level == 0:
			return
		for key, group in groupby(sessions, lambda s: s.name.split(',')[0]):
			group_tee = tee(group, 2)
			print(f'\t{key}: {sumdurations(group_tee[0])/60:.2f}')
			if level > 1:
				for subkey, subgroup in groupby(group_tee[1], lambda s: s.name):
					print(f'\t\t{subkey.split(",",1)[-1]}: {sumdurations(subgroup)/60:.2f}')

	def _reportdays(self, sessions, level):
		for key, group in groupby(sessions, lambda s: s.start.date()):
			group_tee = tee(group, 2)
			print(f'{key}: {sumdurations(group_tee[0])/60:.2f}')
			self._reportday(group_tee[1], level - 1)

	def reportday(self, day, level = 2):
		ss = self._getsessions('''SELECT * FROM sessions WHERE start BETWEEN ? AND ?''',
					[day.replace(hour=0, minute=0, second=0, microsecond=0),
					 day.replace(hour=23, minute=59, second=59, microsecond=999999)])
		print(f'total for {day.date()}: {sumdurations(ss)/60:.2f}')
		self._reportday(ss, level)

	def reportperiod(self, start, end, level = 2):
		ss = self._getsessions('''SELECT * FROM sessions WHERE start BETWEEN ? AND ?''',
					[start.replace(hour=0, minute=0, second=0, microsecond=0),
					 end.replace(hour=23, minute=59, second=59, microsecond=999999)])
		self._reportdays(ss, level)

	def reportname(self, name, level = 2):
		ss = self._getsessions('''SELECT * FROM sessions WHERE name LIKE ?''', [name+'%'])
		print(f'total for {name}: {sumdurations(ss)/60:.2f}')
		self._reportdays(ss, level)

	def reportrunning(self, level = 2):
		ss = self._getsessions('''SELECT * FROM sessions WHERE duration IS NULL''', [])
		self._printsessionstable(ss)

	def _getsessions(self, query, parameters):
		c = self.conn.execute(query, parameters)
		return [self._getsession(row) for row in c]

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
