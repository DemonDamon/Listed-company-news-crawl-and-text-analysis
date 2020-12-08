import __init__

from Kite.database import Database


class Deduplication(object):

    def __init__(self, database_name, collection_name):
        self.database = Database()
        self.database_name = database_name
        self.collection_name = collection_name

    def run(self):
        self.collection = self.database.get_data(self.database_name,
                                                 self.collection_name,
                                                 query={})
