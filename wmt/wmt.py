import argparse
import configparser
import datetime
import csv
import os
import pprint
import time
from .db import Db
from .constants import *

def getUserDir():
	if os.name == 'nt':
		return os.getenv('USERPROFILE')
	elif os.name == 'posix':
		return os.getenv('HOME')
	else:
		raise Exception('Not supported platform - ' + os.name)

class Wmt:
	def __init__(self, debug = False):
		self.debug_prints = debug
		self.debug('initiating wmt')
		# search and parse dotfile:
		self.config_path = os.path.join(getUserDir(), '.wmtconfig')
		self.getconfig()
		self.getdb()

		# we want always to write to this config
		# if os.path.exists(config_path):
		#         config = configparser.ConfigParser()
		#         config.read(config_path)
		#         self.db_path = config['Paths']['DataBaseFile']
		# else:
		#         self.db_path = os.path.join(wmt_path, 'db.csv')
		# if not os.path.exists(self.db_path):
		#         self.create_db()
		# else:
		#         self.debug('db already exist in ' + self.db_path)

	def start(self, name, offset):
		start = datetime.datetime.now()
		start += datetime.timedelta(minutes = offset)
		with self.db.open('a') as f:
			writer = csv.DictWriter(f, fieldnames = COLUMNS_NAMES)
			writer.writerow({'name': name, 'start': start.strftime(DATETIME_FMT)})

		print(name + ' ' + start.strftime(DATETIME_FMT))

	def end(self, offset):
		end = datetime.datetime.now()
		end += datetime.timedelta(minutes = offset)
		with self.db.open('r+') as f:
			reader = csv.DictReader(f, fieldnames = COLUMNS_NAMES)
			for row in reader:
				pass
			if row['end'] != '':
				raise Exception('No session is running')
			name = row['name']
			start = datetime.datetime.strptime(row['start'], DATETIME_FMT)
			print('total sec is ' + str((end - start).total_seconds()))
			print('total sec/60 is ' + str((end - start).total_seconds() / 60))
			duration = int(round((end - start).total_seconds() / 60))

			# removing last line:
			f.seek(0, os.SEEK_END)
			pos = f.tell() - 2
			while pos > 0 and f.read(1) != "\n":
				pos -= 1
				f.seek(pos, os.SEEK_SET)
			pos += 2
			f.seek(pos, os.SEEK_SET)
			f.truncate()

			writer = csv.DictWriter(f, fieldnames = COLUMNS_NAMES)
			writer.writerow({'name': name,
				'start': start.strftime(DATETIME_FMT), 'end': end.strftime(DATETIME_FMT),
				'duration': duration})
		self.db.save()
		print(name + ' ' + start.strftime(DATETIME_FMT) + ' ended (' + str(duration) +' minutes)')

	def status(self):
		with self.db.open('r') as f:
			reader = csv.DictReader(f, fieldnames = COLUMNS_NAMES,)
			for row in reader:
				pass
			pprint.pprint(row)

	def config(self):
		# TODO: select from list (onedrive, local ...)
		print('''Where is My Time?

		''')
		self.config = configparser.RawConfigParser()
		print('auto selecting local file at: C:\\Users\\Idan\\OneDrive\\Documents\\wmtdb.csv')
		self.config.add_section('Paths')
		self.config.set('Paths', 'DataBaseFile', 'C:\\Users\\Idan\\OneDrive\\Documents\\wmtdb.csv')
		with open(self.config_path, 'w') as f:
			self.config.write(f)

	def getconfig(self):
		if not os.path.exists(self.config_path):
			print('No configuration found - please configure:')
			self.config()

		self.config = configparser.ConfigParser()
		self.config.read(self.config_path)
		self.debug('Config file:')
		with open(self.config_path, 'r') as f:
			self.debug(f.read())

	def getdb(self):
		# TODO: create the appropriate db
		self.debug('Getting local file DB')
		self.db =  Db(self.config['Paths']['DataBaseFile'])

	def debug(self, f):
		if self.debug_prints:
			print(f)


def printprogressbar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s        ' % (prefix, bar, percent, suffix), end='\r')

def main():
	parser = argparse.ArgumentParser(description='Find out where your time goes. Simple time-tracer CLI')
	parser.add_argument('action', choices=['start', 'end', 'status', 'config'], help='Possible actions')
	parser.add_argument('-n', '--name', type=str, required=False, help='Name of the session')
	parser.add_argument('-t', '--time', type=int, default=0, required=False, help='Relative time in minutes to start/end the session in')
	parser.add_argument('-d', '--duration', type=int, required=False, help='Duration of the session in minutes')
	parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
	parser.add_argument('-i', '--interactive', help='Interctive wait for session to end', action='store_true')
	args = parser.parse_args()
	wmt = Wmt(args.verbose)

	if args.action == 'start':
		if args.name is None:
			raise Exception('error: the following arguments are required: -n/--name')
		wmt.start(args.name, args.time)
		if args.interactive:
			t0 = time.time()
			elapsed = 0
			print('Hit Ctrl+\'C\' to end this session')
			try:
				while args.duration is None or elapsed < (args.duration * 60):
					elapsed = time.time() - t0
					time.sleep(0.2)
					if args.duration is None:
						print('\rElapsed %s:%s     '%(int(elapsed / 60), round(elapsed % 60)), end='\r')
					else:
						printprogressbar(elapsed, args.duration * 60, prefix='', suffix='Elapsed %s:%s'%(int(elapsed / 60), round(elapsed % 60)))
			except KeyboardInterrupt:
				pass
			print()
			wmt.end(0)
		else:
			if not args.duration is None:
				wmt.end(args.duration)
	elif args.action == 'end':
		wmt.end(args.time)
	elif args.action == 'status':
		wmt.status()
	elif args.action == 'config':
		wmt.config()


if __name__ == "__main__":
	main()
