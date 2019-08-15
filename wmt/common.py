import os
import datetime
import dateparser

def getuserdir():
	if os.name == 'nt':
		return os.getenv('USERPROFILE')
	elif os.name == 'posix':
		return os.getenv('HOME')
	else:
		raise Exception('Not supported platform - ' + os.name)

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
