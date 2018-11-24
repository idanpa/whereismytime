import os

COLUMNS_NAMES = ['start', 'end', 'duration', 'name', 'subname 1', 'subname 2', 'subname 3']
DATETIME_FMT = '%d/%m/%y %H:%M.%S'

def getuserdir():
	if os.name == 'nt':
		return os.getenv('USERPROFILE')
	elif os.name == 'posix':
		return os.getenv('HOME')
	else:
		raise Exception('Not supported platform - ' + os.name)
