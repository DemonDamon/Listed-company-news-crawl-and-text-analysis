from pymongo import MongoClient


class Database(object):

	def __init__(self, ip='localhost', port=27017):
		self.ip = ip
		self.port = port
		self.conn = MongoClient(self.ip, self.port)

	def create_db(self, database_str):
		return self.conn[database_str]

	@staticmethod
	def create_col(database, collection_str):
		return database.get_collection(collection_str)

	@staticmethod
	def insert_data(collection, data_dict):
		# dic = {'name': 'serena', "id": 1532}
		collection.insert_one(data_dict)

	def drop_db(self, database):
		self.conn.drop_database(database)


'''
from database import Database

ExampleObj = Database()
db = ExampleObj.create_db("cnstock")
col = ExampleObj.create_col(db, "cnstock_col")
ExampleObj.insert_data(col, {'name': 'sena', "id": 136})
ExampleObj.drop_db(db)
'''

