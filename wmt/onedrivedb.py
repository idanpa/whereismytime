import os
import onedrivesdk
from onedrivesdk.helpers import GetAuthCodeServer
from .common import *
from .settings import *
from .db import Db

redirect_uri = 'http://localhost:8083/'
scopes=['wl.signin', 'wl.offline_access', 'onedrive.readwrite']
api_base_url='https://api.onedrive.com/v1.0/'
session_file_path = os.path.join(getuserdir(), '.wmtonedrivesession')

ONEDRIVEDB_WMT_DB_PATH = 'Documents/wmt.db'

class OneDriveDb(Db):
	def __init__(self):
		# Authentication:
		self.client = onedrivesdk.get_default_client(client_id=WMT_CLIENT_ID, scopes=scopes)

		self.authenticate()

		local_file_path = os.path.join(getuserdir(), 'wmtdb.csv')
		self.db_file_item = self.client.item(drive='me', path=ONEDRIVEDB_WMT_DB_PATH)
		try:
			self.db_file_item.download(local_file_path)
		# if DB doesn't exist, we wil create it in parent init:
		except onedrivesdk.error.OneDriveError:
			pass

		super().__init__(local_file_path)

	def authenticate(self):
		if os.path.exists(session_file_path):
			self.client.auth_provider.load_session(path=session_file_path)
			self.client.auth_provider.refresh_token()
		else:
			auth_url = self.client.auth_provider.get_auth_url(redirect_uri)
			# this will block until we have the auth code :
			code = GetAuthCodeServer.get_auth_code(auth_url, redirect_uri)
			self.client.auth_provider.authenticate(code, redirect_uri, WMT_CLIENT_SECRET)

		self.client.auth_provider.save_session(path=session_file_path)


	def save(self):
		super().save()
		# TODO: consider update_async()
		# TODO: handle conflicts
		self.db_file_item.upload(self.localpath)
