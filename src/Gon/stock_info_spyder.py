"""
https://waditu.com/document/2
"""
import __init__
from spyder import Spyder

from Kite import config

import tushare as ts
ts.set_token(config.TUSHARE_TOKEN)

import akshare as ak


class StockInfoSpyder(Spyder):

    def __init__(self):
        super(StockInfoSpyder, self).__init__()
        self.db = self.db_obj.create_db(config.TUSHARE_DATABASE_NAME)
        self.col_basic_info = self.db_obj.create_col(self.db, config.COLLECTION_NAME_STOCK_BASIC_INFO)

    def get_stock_code_info(self):
        stock_info_a_code_name_df = ak.stock_info_a_code_name()
        for _id in range(stock_info_a_code_name_df.shape[0]):
            _dict = stock_info_a_code_name_df.iloc[_id].to_dict()
            self.col.insert_one(_dict)

    def get_historical_news(self):
        pass


if __name__ == "__main__":
