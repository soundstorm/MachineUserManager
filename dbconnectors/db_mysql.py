# -*- coding: utf-8 -*-

'''
DB Connector for MySQL
'''
import mysql.connector, time

class db_connector:
	host     = 'localhost'
	user     = 'machines'
	password = 'password'
	database = 'machines'
	port     = 3306
	machine  = 'lasercutter'

	def configure(**kwargs):
		db_connector.host = kwargs['host']
		db_connector.user = kwargs['user']
		db_connector.password = kwargs['password']
		db_connector.database = kwargs['database']
		if 'port' in kwargs:
			db_connector.port = kwargs['port']
		if 'machine' in kwargs:
			db_connector.machine = kwargs['machine']

	def __init__(self, uid):
		self.uid = uid
		self.db = mysql.connector.connect(
			host = db_connector.host,
			user = db_connector.user,
			password = db_connector.password,
			database = db_connector.database,
			port = db_connector.port
		)
		self.cursor = self.db.cursor(dictionary=True)
		self.cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
		self.cursor.execute('SELECT uid FROM alias WHERE card_id = %s', (uid, ))
		result = self.cursor.fetchone()
		if result is not None:
			self.uid = result['uid']
		self.per_login = 0
		self.per_minute = 0
		self.session_valid_until = 0
		self.credit = 0

	def get_user_info(self):
		self.cursor.execute('SELECT IF(name IS NULL OR name = "", HEX(CAST(uid AS UNSIGNED)), name) as name, value FROM cards WHERE uid = %s', (self.uid, ))
		try:
			result = self.cursor.fetchone()
			self.credit = float(result['value'])
			return result['name'], self.credit
		except:
			self.credit = 0.0
			return None, None

	def get_rate(self):
		self.cursor.execute('SELECT r.per_login, r.per_minute FROM authorization a LEFT JOIN rates r ON a.rate = r.rid WHERE a.uid = %s AND a.machine = %s', (self.uid, self.machine))
		try:
			result = self.cursor.fetchone()
			self.per_login = float(result['per_login'])
			self.per_minute = float(result['per_minute'])
			return self.per_login, self.per_minute
		except:
			return None, None

	def is_authorized(self):
		self.cursor.execute('SELECT uid FROM authorization WHERE uid = %s AND machine = %s', (self.uid, self.machine))
		try:
			self.cursor.fetchone()
			return self.cursor.rowcount != 0
		except:
			return False

	def can_create_session(self):
		price = self.per_login + self.per_minute
		self.check_credit()
		return self.credit >= price

	def check_credit(self):
		self.cursor.execute('SELECT value FROM cards WHERE uid = %s', (self.uid, ))
		try:
			result = self.cursor.fetchone()
			self.credit = float(result['value'])
			return self.credit
		except:
			return 0


	def create_session(self):
		self.start_time = int(time.time())
		self.get_rate()
		price = self.per_login + self.per_minute
		try:
			self.cursor.execute('UPDATE cards SET value = (value - %s) WHERE uid = %s AND value >= %s', (price, self.uid, price))
			self.cursor.execute('INSERT INTO sessions (uid, machine, start_time, price) VALUES(%s, %s, %s, %s)', (self.uid, self.machine, self.start_time, -price))
			self.db.commit()
			self.check_credit()
			self.session_valid_until = self.start_time + 60
			return True
		except:
			self.db.rollback()
			return False

	'''
	Check if current session is still valid and extend if neccessary.
	Returns True if still valid or revaluation was successful.
	Returns False if no session was created beforehand or credit is not enough to extend.
	'''
	def extend_session(self):
		if self.session_valid_until == 0:
			return False
		if self.session_valid_until >= time.time():
			return True
		price = self.per_minute
		try:
			self.cursor.execute('UPDATE cards SET value = (value - %s) WHERE uid = %s AND value >= %s', (price, self.uid, price))
			self.cursor.execute('UPDATE sessions SET price = (price - %s) WHERE uid = %s AND machine = %s AND start_time = %s', (price, self.uid, self.machine, self.start_time))
			self.db.commit()
			self.check_credit()
			self.session_valid_until += 60
			return True
		except:
			self.db.rollback()
			return False

	def get_remaining_time(self):
		if self.per_minute is None:
			return 0
		elif self.per_minute == 0:
			return 999
		else:
			return int((self.credit - (self.per_login if self.session_valid_until == 0 else 0)) / self.per_minute)

	def end_session(self):
		self.cursor.execute('UPDATE sessions SET end_time = %s WHERE uid = %s AND machine = %s AND start_time = %s', (int(time.time()), self.uid, self.machine, self.start_time))
		self.db.commit()
		self.session_valid_until = 0
