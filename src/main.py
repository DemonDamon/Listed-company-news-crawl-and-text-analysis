# 1. 爬取历史数据
import time
import logging
from Kite import config
from Gon.jrjspyder import JrjSpyder
from Gon.cnstockspyder import CnStockSpyder
from Gon.nbdspyder import NbdSpyder
from Gon.stockinfospyder import StockInfoSpyder

stock_info_spyder = StockInfoSpyder(config.STOCK_DATABASE_NAME, config.COLLECTION_NAME_STOCK_BASIC_INFO)
stock_info_spyder.get_historical_news()

cnstock_spyder = CnStockSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_CNSTOCK)
for url_to_be_crawled, type_chn in config.WEBSITES_LIST_TO_BE_CRAWLED_CNSTOCK.items():
    logging.info("start crawling {} ...".format(url_to_be_crawled))
    cnstock_spyder.get_historical_news(url_to_be_crawled, category_chn=type_chn)
    logging.info("finished ...")
    time.sleep(30)

jrj_spyder = JrjSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_JRJ)
jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ)

nbd_spyder = NbdSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_NBD)
nbd_spyder.get_historical_news(684)  # 可以设置参数为"684"，但数据量较大，爬取时间较长(大概为1周)，因此这里设置为5


# 2. 针对历史数据进行去重清洗
from Killua.deduplication import Deduplication

Deduplication(config.DATABASE_NAME, config.COLLECTION_NAME_CNSTOCK).run()
Deduplication(config.DATABASE_NAME, config.COLLECTION_NAME_NBD).run()
Deduplication(config.DATABASE_NAME, config.COLLECTION_NAME_JRJ).run()


# 3. 将历史数据中包含null值的行去掉
from Killua.denull import DeNull

DeNull(config.DATABASE_NAME, config.COLLECTION_NAME_CNSTOCK).run()
DeNull(config.DATABASE_NAME, config.COLLECTION_NAME_NBD).run()
DeNull(config.DATABASE_NAME, config.COLLECTION_NAME_JRJ).run()


# 4. 创建新的数据库，针对每一个股票，将所有涉及该股票的新闻都保存在新的数据库，并贴好"利好","利空"和"中性"标签
from Killua.buildstocknewsdb import GenStockNewsDB

gen_stock_news_db = GenStockNewsDB()
gen_stock_news_db.get_all_news_about_specific_stock(config.DATABASE_NAME, config.COLLECTION_NAME_CNSTOCK)
gen_stock_news_db.get_all_news_about_specific_stock(config.DATABASE_NAME, config.COLLECTION_NAME_NBD)
gen_stock_news_db.get_all_news_about_specific_stock(config.DATABASE_NAME, config.COLLECTION_NAME_JRJ)


# 5. 开启实时爬取新闻数据
