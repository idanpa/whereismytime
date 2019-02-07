# coding=utf-8

import argparse
import configparser
import os
import sys
import time
import datetime
import dateparser
from .db import Db
from .db import WmtSession
from .onedrivedb import OneDriveDb
from .common import *

DB_SECTION_NAME = 'DB'
NAMES_DELIMITER = ','

def ehandler(exctype, value, tb):
	print(str(exctype.__name__) + ': ' + str(value))

# TODO: consider remove this class
class Wmt:
	def __init__(self):
		self.getconfig()
		self.getdb()

	def getconfigfromuser(self):
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
			default_local_file_path = os.path.join(getuserdir(), 'wmt.db')
			local_file_path = input("Please write local DB path, or leave empty to use default:")
			if local_file_path == '':
				local_file_path = default_local_file_path
			print('DB file is in ' + local_file_path)
			self.config.set(DB_SECTION_NAME, 'DataBaseFile', local_file_path)

		with open(self.config_path, 'w') as f:
			self.config.write(f)

	def getconfig(self):
		# search and parse dotfile:
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

	def getdb(self):
		db_type_code = self.config.getint(DB_SECTION_NAME, 'DataBaseType')
		if db_type_code == 1:
			self.db = Db(self.config[DB_SECTION_NAME]['DataBaseFile'])
		elif db_type_code == 2:
			self.db = OneDriveDb()
		else:
			raise Exception('Not supported DB type: ' + str(db_type_code))

def printprogressbar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print('\r%s |%s| %s%% %s        ' % (prefix, bar, percent, suffix), end='\r')

def parsetime(time_str):
	if time_str and time_str.strip():
		try:
			minutes_delta = int(time_str)
			tm = datetime.datetime.now() + datetime.timedelta(minutes = minutes_delta)
		except ValueError:
			tm = dateparser.parse(time_str)
		if tm:
			return tm.replace(microsecond = 0)
		else:
			raise ValueError('Could not parse \'' + time_str + '\' to datetime')
	else:
		return None

def main():
	if not __debug__:
		sys.excepthook = ehandler

	# aux parser for global commands (can be parsed at any position)
	global_parser = argparse.ArgumentParser(add_help=False)
	global_parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
	global_parser.add_argument('-i', '--interactive', help='Interactive wait for session to end', action='store_true')
	global_parser.add_argument('-y', '--yes', help='Suppress warning', action='store_true')

	# create the top-level parser
	parser = argparse.ArgumentParser(description='Find out where is your time. Simple time management CLI.', prog='wmt', parents=[global_parser])
	subparsers = parser.add_subparsers(help='sub-command help', dest='command')

	start_parser = subparsers.add_parser('start', help='starts new session', parents=[global_parser])
	start_parser.add_argument('-n', '--name', type=str, required=False, help='Name of the session')
	start_parser.add_argument('-t', '--time', type=str, default='0', required=False, help='Relative time in minutes to start the session in (e.g. -15), or absolute time (e.g 14:12 or yesterday at 8:10). Defaults to current time')
	start_parser.add_argument('-d', '--duration', type=int, required=False, help='Duration of the session in minutes')
	start_parser.add_argument('-e', '--endtime', type=str, required=False, help='Relative time in minutes to end the session in (e.g. -15), or absolute time (e.g 14:12 or yesterday at 8:10)')

	end_parser = subparsers.add_parser('end', help='ends a session', parents=[global_parser])
	end_parser.add_argument('-id', '--id', type=int, default=None, required=False, help='Session id to end, default value would end last session')
	end_parser.add_argument('-t', '--time', type=str, default='0', required=False, help='Relative time in minutes to start the session in (e.g. -15), or absolutetime (e.g 14:12 or yesterday at 8:10). Defaults to current time')

	config_parser = subparsers.add_parser('config', help='configure', parents=[global_parser])

	edit_parser = subparsers.add_parser('edit', help='edit session', parents=[global_parser])
	edit_parser.add_argument('-id', '--id', type=int, default=None, required=False, help='Session id to edit, default value would edit last session')
	edit_parser.add_argument('-n', '--name', type=str, required=False, help='Name of the session')
	edit_parser.add_argument('-s', '--starttime', type=str, default=None, required=False, help='Relative time in minutes to set the start of the session in (e.g. -15), or absolute time (e.g 14:12 or yesterday at 8:10).')
	edit_parser.add_argument('-e', '--endtime', type=str, default=None, required=False, help='Relative time in minutes to set the end of the session in (e.g. -15), or absolute time (e.g 14:12 or yesterday at 8:10)')
	edit_parser.add_argument('-d', '--duration', type=int, default=None, required=False, help='Duration of the session in minutes')

	del_parser = subparsers.add_parser('rm', help='delete session', parents=[global_parser])
	del_parser.add_argument('-id', '--id', type=int, default=None, required=False, help='Session id to be deleted, default value would delete last session')

	import_parser = subparsers.add_parser('import', help='Import sessions from csv file', parents=[global_parser])
	import_parser.add_argument('filepath', type=str, help='csv file path to import')

	export_parser = subparsers.add_parser('export', help='Export sessions to csv file', parents=[global_parser])
	export_parser.add_argument('filepath', type=str, help='csv file path to export')

	report_parser = subparsers.add_parser('report', help='Export sessions to csv file', parents=[global_parser])
	report_subparsers = report_parser.add_subparsers(help='report type', dest='report_type')
	day_parser = report_subparsers.add_parser('day', help='show specific day sessions')
	day_parser.add_argument('day', type=str, default='0', nargs='?', help='day')
	period_parser = report_subparsers.add_parser('period', help='show sessions over given period')
	period_parser.add_argument('period', type=str, nargs='+', help='defined by 2 strings of times, if only one string supplied would consder until current time')
	last_parser = report_subparsers.add_parser('last', help='show N last sessions')
	last_parser.add_argument('number', type=int, default=10, nargs='?', help='Number of last sessions to show')
	name_parser = report_subparsers.add_parser('name', help='filter sessions by name')
	name_parser.add_argument('name', type=str, help='Show sessions with name starting with given string')
	report_subparsers.add_parser('running', help='Show all running sessions')

	args = parser.parse_args()
	wmt = Wmt()

	# make a guess if no command was supplied:
	if args.command is None:
		# TODO: also support start/end etc for the case of the start
		if wmt.is_session_running():
			args = parser.parse_args(args = ['end'])
		else:
			args = parser.parse_args(args = ['start'])

	if args.command == 'start':
		if (not args.duration is None) and (not args.endtime is None):
			raise Exception('Please supply either end or duration, can\'t handle both')

		t0 = parsetime(args.time)
		s = WmtSession(input('Session name:') if args.name is None else args.name, t0)

		if not args.endtime is None:
			s.setend(parsetime(args.endtime))
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
			s.setend(datetime.datetime.now())
		else:
			if not args.duration is None:
				s.setend(t0 + datetime.timedelta(minutes = args.duration))
		wmt.db.insertsession(s)
		wmt.db.save()
		print(s)
	elif args.command == 'end':
		s = wmt.db.getsession(args.id)
		if s.duration is None:
			s.setend(parsetime(args.time))
			wmt.db.setsession(s)
			wmt.db.save()
			print(s)
		else:
			print('Session was already ended.')
	elif args.command == 'edit':
		s = wmt.db.getsession(args.id)
		if not args.name is None:
			s.name = args.name
		if not args.starttime is None:
			s.start = parsetime(args.starttime)
		if not args.endtime is None:
			s.setend(parsetime(args.endtime))
		elif not args.duration is None:
			s.duration = args.duration
		wmt.db.setsession(s)
		wmt.db.save()
	elif args.command == 'rm':
		if args.yes or input('Drop session - ' + str(wmt.db.getsession(args.id)) + '? (y/N): ').lower() == 'y':
			wmt.db.dropsession(args.id)
			print('Session dropped')
	elif args.command == 'import':
		wmt.db.importcsv(args.filepath)
	elif args.command == 'export':
		wmt.db.exportcsv(args.filepath)
	elif args.command == 'report':
		if args.report_type == 'day':
			day = parsetime(args.day)
			wmt.db.reportday(day)
		elif args.report_type == 'period':
			start = parsetime(args.period[0])
			if len(args.period) > 1:
				end = parsetime(args.period[1])
			else:
				end = datetime.datetime.now()
			wmt.db.reportperiod(start, end)
		elif args.report_type == 'name':
			wmt.db.reportname(args.name)
		elif args.report_type == 'running':
			wmt.db.reportrunning()
		elif args.report_type == 'last':
			wmt.db.reportlast(args.number)
		elif args.report_type is None:
			wmt.db.reportday(datetime.datetime.now())
	elif args.command == 'config':
		wmt.getconfigfromuser()

if __name__ == "__main__":
	main()
