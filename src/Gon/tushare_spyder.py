"""
https://waditu.com/document/2
"""
import __init__
from spyder import Spyder

from Kite import config

import tushare as ts
ts.set_token(config.TUSHARE_TOKEN)

import akshare as ak

class TushareSpyder(Spyder):

    def __init__(self):
        super(TushareSpyder, self).__init__()
        self.db = self.db_obj.create_db(config.TUSHARE_DATABASE_NAME)
        self.col_basic_info = self.db_obj.create_col(self.db, config.COLLECTION_NAME_STOCK_BASIC_INFO)
        stock_info_a_code_name_df = ak.stock_info_a_code_name()
        stock_info_a_code_name_df.iloc[0].to_dict()

    def get_stock_code

    def get_historical_news