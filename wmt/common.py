import os

def getuserdir():
	if os.name == 'nt':
		return os.getenv('USERPROFILE')
	elif os.name == 'posix':
		return os.getenv('HOME')
	else:
		raise Exception('Not supported platform - ' + os.name)
