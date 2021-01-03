"""
https://waditu.com/document/2
"""
import __init__

import os
import time
import logging
import datetime
from spyder import Spyder

from pandas._libs.tslibs.timestamps import Timestamp

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
        self.start_program_date = datetime.datetime.now().strftime("%Y%m%d")

    def get_stock_code_info(self):
        stock_info_df = ak.stock_info_a_code_name()  # 获取所有A股code和name
        stock_symbol_code = ak.stock_zh_a_spot().get(["symbol", "code"])  # 获取A股所有股票的symbol和code
        for _id in range(stock_info_df.shape[0]):
            _symbol = stock_symbol_code[stock_symbol_code.code == stock_info_df.iloc[_id].code].symbol.values
            if len(_symbol) != 0:
                _dict = {"symbol": _symbol[0]}
                _dict.update(stock_info_df.iloc[_id].to_dict())
                self.col_basic_info.insert_one(_dict)

    def get_historical_news(self, start_date=None, end_date=None, freq="day"):
        if end_date is None:
            end_date = datetime.datetime.now().strftime("%Y%m%d")
        stock_symbol_list = self.col_basic_info.distinct("symbol")
        if len(stock_symbol_list) == 0:
            self.get_stock_code_info()
            stock_symbol_list = self.col_basic_info.distinct("symbol")
        if freq == "day":
            if os.path.exists(config.STOCK_DAILY_EXCEPTION_TXT_FILE_PATH):
                with open(config.STOCK_DAILY_EXCEPTION_TXT_FILE_PATH, "r") as file:
                    start_stock_code = file.read()
                logging.info("read {} to get start code number is {} ... "
                             .format(config.STOCK_DAILY_EXCEPTION_TXT_FILE_PATH, start_stock_code))
            else:
                start_stock_code = 0
            for symbol in stock_symbol_list:
                if int(symbol[2:]) > 603185: #>= int(start_stock_code):
                    try:
                        if start_date is None:
                            # 如果该symbol有历史数据，如果有则从API获取从数据库中最近的时间开始直到现在的所有价格数据
                            # 如果该symbol无历史数据，则从API获取从2015年1月1日开始直到现在的所有价格数据
                            symbol_date_list = self.db_obj.get_data(self.database_name, symbol, keys=["date"])["date"].to_list()
                            if len(symbol_date_list) == 0:
                                start_date = config.STOCK_PRICE_REQUEST_DEFAULT_DATE
                            else:
                                tmp_date = str(max(symbol_date_list)).split(" ")[0]
                                tmp_date_dt = datetime.datetime.strptime(tmp_date, "%Y-%m-%d").date()
                                offset = datetime.timedelta(days=1)
                                start_date = (tmp_date_dt + offset).strftime('%Y%m%d')
                        stock_zh_a_daily_hfq_df = ak.stock_zh_a_daily(symbol=symbol,
                                                                      start_date=start_date,
                                                                      end_date=end_date,
                                                                      adjust="qfq")
                        stock_zh_a_daily_hfq_df.insert(0, 'date', stock_zh_a_daily_hfq_df.index.tolist())
                        stock_zh_a_daily_hfq_df.index = range(len(stock_zh_a_daily_hfq_df))
                        _col = self.db_obj.get_collection(self.database_name, symbol)
                        for _id in range(stock_zh_a_daily_hfq_df.shape[0]):
                            _tmp_dict = stock_zh_a_daily_hfq_df.iloc[_id].to_dict()
                            _tmp_dict.pop("outstanding_share")
                            _tmp_dict.pop("turnover")
                            _col.insert_one(_tmp_dict)
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

    def get_realtime_news(self, freq="day"):
        while True:
            if freq == "day":
                time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_time = "{} {}".format(time_now.split(" ")[0], "15:30:00")
                if time_now >= update_time:
                    stock_zh_a_spot_df = ak.stock_zh_a_spot()  # 当天的日数据行情下载
                    for _id, sym in enumerate(stock_zh_a_spot_df["symbol"]):
                        _col = self.db_obj.get_collection(self.database_name, sym)
                        _tmp_dict = {}
                        _tmp_dict.update({"date": Timestamp("{} 00:00:00".format(time_now.split(" ")[0]))})
                        _tmp_dict.update({"open": stock_zh_a_spot_df.iloc[_id].open})
                        _tmp_dict.update({"high": stock_zh_a_spot_df.iloc[_id].high})
                        _tmp_dict.update({"low": stock_zh_a_spot_df.iloc[_id].low})
                        _tmp_dict.update({"close": stock_zh_a_spot_df.iloc[_id].trade})
                        _tmp_dict.update({"volume": stock_zh_a_spot_df.iloc[_id].volume})
                        _col.insert_one(_tmp_dict)
                        logging.info("finished updating {} price data of {} ... ".format(symbol, time_now.split(" ")[0]))


if __name__ == "__main__":
    stock_info_spyder = StockInfoSpyder(config.STOCK_DATABASE_NAME, config.COLLECTION_NAME_STOCK_BASIC_INFO)

    # 指定时间段，获取历史数据，如：stock_info_spyder.get_historical_news(start_date="20150101", end_date="20201204")
    # 如果没有指定时间段，且数据库已存在部分数据，则从最新的数据时间开始获取直到现在，比如数据库里已有sh600000价格数据到
    # 2020-12-03号，如不设定具体时间，则从自动获取sh600000自2020-12-04至当前的价格数据
    # stock_info_spyder.get_historical_news()

    from pymongo import MongoClient

    db = MongoClient("localhost", 27017)
    col_basic_info = db["stock"].get_collection("basic_info")
    stock_symbol_list = col_basic_info.distinct("symbol")

    for sym in stock_symbol_list:
        _col = db["stock"].get_collection(sym)
        for _ in _col.find():
            _col.update_one(filter={"outstanding_share": {"$exists": True}}, update = {"$unset": {"outstanding_share": ""}},upsert = False)
            _col.update_one(filter={"turnover": {"$exists": True}}, update = {"$unset": {"turnover": ""}}, upsert = False)
        print("{} drop outstanding_share and turnover keys ... ".format(sym))
    print("更新完毕")