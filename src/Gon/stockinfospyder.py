"""
https://waditu.com/document/2
"""
import __init__

import os
import logging
from spyder import Spyder

from Kite.database import Database
from Kite import config

import akshare as ak

import tushare as ts
ts.set_token(config.TUSHARE_TOKEN)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class StockInfoSpyder(Spyder):

    def __init__(self, database_name, collection_name):
        super(StockInfoSpyder, self).__init__()
        self.db_obj = Database()
        self.col_basic_info = self.db_obj.get_collection(database_name, collection_name)
        self.database_name = database_name
        self.collection_name = collection_name

    def get_stock_code_info(self):
        stock_info_df = ak.stock_info_a_code_name()  # 获取所有A股code和name
        stock_symbol_code = ak.stock_zh_a_spot().get(["symbol", "code"])  # 获取A股所有股票的symbol和code
        for _id in range(stock_info_df.shape[0]):
            _symbol = stock_symbol_code[stock_symbol_code.code == stock_info_df.iloc[_id].code].symbol.values
            if len(_symbol) != 0:
                _dict = {"symbol": _symbol[0]}
                _dict.update(stock_info_df.iloc[_id].to_dict())
                self.col_basic_info.insert_one(_dict)
        return stock_info_df

    def get_historical_news(self, start_date, end_date, freq="day"):
        stock_symbol_list = self.col_basic_info.distinct("symbol")
        if len(stock_symbol_list) == 0:
            stock_symbol_list = self.get_stock_code_info()
        if freq == "day":
            if os.path.exists(config.STOCK_DAILY_EXCEPTION_TXT_FILE_PATH):
                with open(config.STOCK_DAILY_EXCEPTION_TXT_FILE_PATH, "r") as file:
                    start_stock_code = file.read()
                logging.info("read {} to get start code number is {} ... "
                             .format(config.STOCK_DAILY_EXCEPTION_TXT_FILE_PATH, start_stock_code))
            else:
                start_stock_code = 0
            for symbol in stock_symbol_list:
                if int(symbol[2:]) >= int(start_stock_code):
                    try:
                        stock_zh_a_daily_hfq_df = ak.stock_zh_a_daily(symbol=symbol,
                                                                      start_date=start_date,
                                                                      end_date=end_date,
                                                                      adjust="hfq")
                        stock_zh_a_daily_hfq_df.insert(0, 'date', stock_zh_a_daily_hfq_df.index.tolist())
                        stock_zh_a_daily_hfq_df.index = range(len(stock_zh_a_daily_hfq_df))
                        _col = self.db_obj.get_collection(self.database_name, symbol)
                        for _id in range(stock_zh_a_daily_hfq_df.shape[0]):
                            _col.insert_one(stock_zh_a_daily_hfq_df.iloc[_id].to_dict())
                        logging.info("{} finished saving ... ".format(symbol))
                    except Exception:
                        with open(config.STOCK_DAILY_EXCEPTION_TXT_FILE_PATH, "w") as file:
                            file.write(symbol[2:])
        elif freq == "week":
            pass
        elif freq == "month":
            pass
        elif freq == "5mins":
            pass
        elif freq == "15mins":
            pass
        elif freq == "30mins":
            pass
        elif freq == "60mins":
            pass


if __name__ == "__main__":
    stock_info_spyder = StockInfoSpyder(config.STOCK_DATABASE_NAME, config.COLLECTION_NAME_STOCK_BASIC_INFO)
    stock_info_spyder.get_stock_code_info()
    # stock_info_spyder.get_historical_news("20150101", "20201204")
