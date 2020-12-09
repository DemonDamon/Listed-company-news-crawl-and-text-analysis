import __init__
import logging

from Kite import config
from Kite.database import Database
from Leorio.tokenization import Tokenization

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class GenStockNewsDB(object):

    def __init__(self):
        self.database = Database()

    def get_all_news_about_specific_stock(self, database_name, collection_name):
        # 获取collection_name的key值，看是否包含RelatedStockCodes，如果没有说明，没有做将新闻中所涉及的
        # 股票代码保存在新的一列
        _keys_list = list(next(self.database.get_collection(database_name, collection_name).find()).keys())
        if "RelatedStockCodes" not in _keys_list:
            tokenization = Tokenization(import_module="jieba", user_dict="./Leorio/financedict.txt")
            tokenization.update_news_database_rows(database_name, collection_name)
        # 创建stock_code为名称的collection
        stock_code_list = self.database.get_data("stock", "basic_info", keys=["code"])["code"].to_list()
        for code in stock_code_list:
            _collection = self.database.get_collection(config.ALL_NEWS_OF_SPECIFIC_STOCK_DATABASE, code)
            _tmp_num_stat = 0
            for row in self.database.get_collection(database_name, collection_name).find():  # 迭代器
                if code in row["RelatedStockCodes"].split(" "):
                    _collection.insert_one({"Date": row["Date"],
                                            "Url": row["Url"],
                                            "Title": row["Title"],
                                            "Article": row["Article"],
                                            "OriDB": database_name,
                                            "OriCOL": collection_name})
                    _tmp_num_stat += 1
            logging.info("there are {} news mentioned {} in {} collection ... "
                         .format(_tmp_num_stat, code, collection_name))


if __name__ == "__main__":
    gen_stock_news_db = GenStockNewsDB()
    gen_stock_news_db.get_all_news_about_specific_stock("finnewshunter", "cnstock")

