import os
import csv
from .common import *

class Db:
	def __init__(self, localpath):
		self.localpath = localpath
		if not os.path.exists(self.localpath):
        		self.create_db()

	def open(self, mode):
		return open(self.localpath, mode, newline='')

	def save(self):
		pass

	def create_db(self):
                with self.open('x') as f:
                        writer = csv.DictWriter(f, fieldnames = COLUMNS_NAMES)
                        writer.writeheader()
