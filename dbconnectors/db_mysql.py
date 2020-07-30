# -*- coding: utf-8 -*-

'''
DB Connector for MySQL
'''
import mysql.connector

class db_connector:
	def __init__(self, **kwargs):
		self.machine = kwargs['machine']
		self.db = mysql.connector.connect(
			host = kwargs['host'],
			user = kwargs['user'],
			password = kwargs['password'],
			database = kwargs['database']
		)
		self.cursor = self.db.cursor()

	def get_alias(self, uid):
		self.cursor.execute("SELECT uid FROM alias WHERE card_id = %s", (uid, ))
		try:
			result = self.cursor.fetchone()
			print(result)
			return result[0]
		except:
			return None

	def get_user_info(self, uid):
		self.cursor.execute('SELECT name, credit FROM cards WHERE uid = %s', (str(uid), ))
		try:
			result = self.cursor.fetchone()
			return result[0], result[1]
		except:
			return None

	def is_authorized(self, uid):
		self.cursor.execute('SELECT COUNT(uid) FROM authorization WHERE uid = %s AND machine = %s', (str(uid), self.machine))
		try:
			self.cursor.fetchone()
			return self.cursor.rowcount != 0
		except:
			return False

	def change_card_value(self, uid, amount):
		self.cursor.execute('UPDATE cards SET credit = (credit + %s) WHERE uid = %s AND credit >= (-%s)', (str(amount), str(uid), str(amount)))
		self.db.commit()
		return self.cursor.rowcount != 0

	def create_session(self, uid, start_time, price):
		self.cursor.execute('INSERT INTO sessions (uid, machine, start_time, price) VALUES(%s, %s, %s, %s)', (uid, self.machine, str(start_time), str(price)))
		self.db.commit()

	def update_session(self, uid, start_time, price):
		self.cursor.execute('UPDATE sessions SET price = price + %s WHERE uid = %s AND machine = %s AND start_time = %s', (str(price), str(uid), self.machine, str(start_time)))
		self.db.commit()

	def end_session(self, uid, start_time, end_time):
		self.cursor.execute('UPDATE sessions SET end_time = %s WHERE uid = %s AND machine = %s AND start_time = %s', (str(end_time), str(uid), self.machine, str(start_time)))
		self.db.commit()
