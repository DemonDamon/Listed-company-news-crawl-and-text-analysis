from Kite import config
from Killua.buildstocknewsdb import GenStockNewsDB


gen_stock_news_db = GenStockNewsDB()
gen_stock_news_db.listen_redis_queue()