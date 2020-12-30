# 1. 爬取历史数据
import time
import logging
from Kite import config
from Gon.jrjspyder import JrjSpyder
from Gon.cnstockspyder import CnStockSpyder
from Gon.nbdspyder import NbdSpyder
from Gon.stockinfospyder import StockInfoSpyder

# stock_info_spyder = StockInfoSpyder(config.STOCK_DATABASE_NAME, config.COLLECTION_NAME_STOCK_BASIC_INFO)
# stock_info_spyder.get_historical_news()

# cnstock_spyder = CnStockSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_CNSTOCK)
# for url_to_be_crawled, type_chn in config.WEBSITES_LIST_TO_BE_CRAWLED_CNSTOCK.items():
#     logging.info("start crawling {} ...".format(url_to_be_crawled))
#     cnstock_spyder.get_historical_news(url_to_be_crawled, category_chn=type_chn)
#     logging.info("finished ...")
#     time.sleep(30)
#
# jrj_spyder = JrjSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_JRJ)
# jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, "2020-12-04", "2020-12-08")
#
# nbd_spyder = NbdSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_NBD)
# nbd_spyder.get_historical_news(684)


# # 2. 抽取出新闻中所涉及的股票，并保存其股票代码在collection中新的一列
# from Leorio.tokenization import Tokenization
#
# tokenization = Tokenization(import_module="jieba", user_dict="./Leorio/financedict.txt")
# tokenization.update_news_database_rows(config.DATABASE_NAME, "cnstock")
# tokenization.update_news_database_rows(config.DATABASE_NAME, "nbd")
# tokenization.update_news_database_rows(config.DATABASE_NAME, "jrj")


# 2. 针对历史数据进行去重清洗
from Killua.deduplication import Deduplication

# Deduplication("finnewshunter", "cnstock").run()
# Deduplication("finnewshunter", "nbd").run()
# Deduplication("finnewshunter", "jrj").run()  # 暂时只有jrj需要去重


# 3. 将历史数据中包含null值的行去掉
from Killua.denull import DeNull

# DeNull("finnewshunter", "cnstock").run()
# DeNull("finnewshunter", "nbd").run()
# DeNull("finnewshunter", "jrj").run()


# 4. 创建新的数据库，针对每一个股票，将所有涉及该股票的新闻都保存在新的数据库，并贴好"利好","利空"和"中性"标签
from Killua.buildstocknewsdb import GenStockNewsDB
# gen_stock_news_db = GenStockNewsDB()
# gen_stock_news_db.get_all_news_about_specific_stock("finnewshunter", "cnstock")
# gen_stock_news_db.get_all_news_about_specific_stock("finnewshunter", "nbd")
# gen_stock_news_db.get_all_news_about_specific_stock("finnewshunter", "jrj")


# 5.
