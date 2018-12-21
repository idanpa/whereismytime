# coding=utf-8

import argparse
import configparser
import csv
import sys
import os
import time
import datetime
import dateparser
import itertools
from .db import Db
from .onedrivedb import OneDriveDb
from .common import *

DB_SECTION_NAME = 'DB'

class Wmt:
	def __init__(self, debug = False):
		self.debug_prints = debug
		self.debug('initiating wmt')
		# search and parse dotfile:
		self.getconfig()
		self.getdb()

	def start(self, name, time):
		with self.db.open('a') as f:
			writer = csv.DictWriter(f, fieldnames = COLUMNS_NAMES)
			names = name.split(writer.writer.dialect.delimiter)
			row = {}
			row['start'] = time.isoformat()
			row['name'] = names[0]
			for i in range(1, min(4, len(names))):
				row['subname ' + str(i)] = names[i]
			writer.writerow(row)

		# TODO: no need to save here, but need to know not to download from server again before ending
		self.db.save()
		print(name + ' ' + time.isoformat())

	def is_session_running(self):
		with self.db.open('r') as f:
			reader = csv.DictReader(f, fieldnames = COLUMNS_NAMES)
			for row in reader:
				pass
			return row['end'] == ''

	def end(self, time):
		with self.db.open('r+') as f:
			reader = csv.DictReader(f, fieldnames = COLUMNS_NAMES)
			for row in reader:
				pass
			if row['end'] != '':
				raise Exception('No session is running')
			name = row['name']
			if sys.version_info[0] > 3 or (sys.version_info[0] == 3 and sys.version_info[1] > 7):
				start = datetime.datetime.fromisoformat(row['start'])
			else:
				start = datetime.datetime.strptime(row['start'], "%Y-%m-%dT%H:%M:%S")
			duration = int(round((time - start).total_seconds() / 60))

			# removing last line:
			f.seek(0, os.SEEK_END)
			pos = f.tell() - 2
			while pos > 0 and f.read(1) != "\n":
				pos -= 1
				f.seek(pos, os.SEEK_SET)
			pos += 1
			f.seek(pos, os.SEEK_SET)
			f.truncate()

			row['end'] = time.isoformat()
			row['duration'] = duration

			writer = csv.DictWriter(f, fieldnames = COLUMNS_NAMES)
			writer.writerow(row)
		self.db.save()
		print(name + ' ' + start.isoformat() + ' ended (' + str(duration) +' minutes)')

	def log(self, n):
		table_format = "{:<10}" + "{:<20}" * len(COLUMNS_NAMES)

		with self.db.open('r') as f:
			reader = csv.reader(f)
			line_count = sum(1 for i in reader)
			f.seek(0)
			reader.__init__(f)

			# print header:
			print(table_format.format("index", *next(reader)))

			i = max(1, line_count - n)
			for row in itertools.islice(reader, max(0, line_count - n - 1), line_count):
				print(table_format.format(i, *row))
				i += 1

	def getconfigfromuser(self):
		print('''Where is My Time?
		''')
		self.config = configparser.RawConfigParser()
		self.config.add_section(DB_SECTION_NAME)

		while True:
			db_type_str = input(
'''Select database type:
	1. Local file
	2. OneDrive
''')
			try:
				db_type_code = int(db_type_str)
				if 0 < db_type_code < 3:
					break
			except:
				pass
			print('Wrong value')

		self.config.set(DB_SECTION_NAME, 'DataBaseType', db_type_code)
		if db_type_code == 1:
			default_local_file_path = os.path.join(getuserdir(), 'wmtdb.csv')
			local_file_path = input("Please write local DB path, or leave empty to use default:")
			if local_file_path == '':
				local_file_path = default_local_file_path
			print('DB file is in ' + local_file_path)
			self.config.set(DB_SECTION_NAME, 'DataBaseFile', local_file_path)

		with open(self.config_path, 'w') as f:
			self.config.write(f)

	def getconfig(self):
		self.config_path = os.path.join(getuserdir(), '.wmtconfig')
		if not os.path.exists(self.config_path):
			print('No configuration found - please configure:')
			self.getconfigfromuser()
		try:
			self.config = configparser.ConfigParser()
			self.config.read(self.config_path)
			self.config.getint(DB_SECTION_NAME, 'DataBaseType')

		except Exception as e:
			print(e)
			self.getconfigfromuser()
			self.config = configparser.ConfigParser()
			self.config.read(self.config_path)

		self.debug('Config file:')
		with open(self.config_path, 'r') as f:
			self.debug(f.read())

	def getdb(self):
		db_type_code = self.config.getint(DB_SECTION_NAME, 'DataBaseType')
		if db_type_code == 1:
			self.db = Db(self.config[DB_SECTION_NAME]['DataBaseFile'])
		elif db_type_code == 2:
			self.db = OneDriveDb()
		else:
			raise Exception('Not supported DB type: ' + str(db_type_code))

	def debug(self, f):
		if self.debug_prints:
			print(f)


def printprogressbar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s        ' % (prefix, bar, percent, suffix), end='\r')

def parsetime(time_str):
	try:
		minutes_delta = int(time_str)
		tm = datetime.datetime.now() + datetime.timedelta(minutes = minutes_delta)
	except ValueError:
		tm = dateparser.parse(time_str)
	return tm.replace(microsecond = 0)

def main():
	# aux parser for global commands (can be parsed at any position)
	global_parser = argparse.ArgumentParser(add_help=False)
	global_parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
	global_parser.add_argument('-i', '--interactive', help='Interactive wait for session to end', action='store_true')

	# create the top-level parser
	parser = argparse.ArgumentParser(description='Find out where is your time. Simple time management CLI.', prog='wmt', parents=[global_parser])
	subparsers = parser.add_subparsers(help='sub-command help', dest='command')

	start_parser = subparsers.add_parser('start', help='starts new session', parents=[global_parser])
	start_parser.add_argument('-n', '--name', type=str, required=False, help='Name of the session')
	start_parser.add_argument('-t', '--time', type=str, default='0', required=False, help='Relative time in minutes to start the session in (e.g. -15), or absolute time (e.g 14:12 or yesterday at 8:10). Defaults to current time')
	start_parser.add_argument('-d', '--duration', type=int, required=False, help='Duration of the session in minutes')
	start_parser.add_argument('-e', '--endtime', type=str, required=False, help='Relative time in minutes to end the session in (e.g. -15), or absolute time (e.g 14:12 or yesterday at 8:10)')

	end_parser = subparsers.add_parser('end', help='ends a session', parents=[global_parser])
	end_parser.add_argument('-t', '--time', type=str, default='0', required=False, help='Relative time in minutes to start the session in (e.g. -15), or absolutetime (e.g 14:12 or yesterday at 8:10). Defaults to current time')

	end_parser = subparsers.add_parser('log', help='show log of sessions', parents=[global_parser])
	end_parser.add_argument('-n', '--number', type=int, default=10, required=False, help='Number of sessions to show')

	end_parser = subparsers.add_parser('config', help='configure', parents=[global_parser])

	args = parser.parse_args()
	wmt = Wmt(args.verbose)

	# make a guess if no command was supplied:
	if args.command is None:
		if wmt.is_session_running():
			args = parser.parse_args(args = ['end'])
		else:
			args = parser.parse_args(args = ['start'])

	if args.command == 'start':
		if (not args.duration is None) and (not args.endtime is None):
			raise Exception('Please supply either end or duration, can\'t handle both')

		t0 = parsetime(args.time)
		wmt.start(input('Session name:') if args.name is None else args.name, t0)

		if not args.endtime is None:
			wmt.end(parsetime(args.endtime))
		elif args.interactive:
			elapsed = 0
			print('Hit Ctrl+\'C\' to end this session')
			try:
				while args.duration is None or elapsed < (args.duration * 60):
					elapsed_secs = (datetime.datetime.now() - t0).total_seconds()
					hours, remainder = divmod(abs(elapsed_secs), 3600)
					minutes, seconds = divmod(remainder, 60)
					elapsed_str = 'Elapsed {}{:02}:{:02}:{:02}         '.format('-' if elapsed_secs < 0 else '', int(hours), int(minutes), int(seconds))
					time.sleep(0.2)
					if args.duration is None:
						print('\r' + elapsed_str, end='\r')
					else:
						printprogressbar(elapsed_secs, args.duration * 60, prefix='', suffix=elapsed_str)
			except KeyboardInterrupt:
				pass
			print()
			wmt.end(datetime.datetime.now())
		else:
			if not args.duration is None:
				wmt.end(t0 + datetime.timedelta(minutes = args.duration))
	elif args.command == 'end':
		wmt.end(parsetime(args.time))
	elif args.command == 'log':
		wmt.log(args.number)
	elif args.command == 'config':
		wmt.getconfigfromuser()

if __name__ == "__main__":
	main()
