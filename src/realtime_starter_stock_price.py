from Kite import config
from Gon.stockinfospyder import StockInfoSpyder


stock_info_spyder = StockInfoSpyder(config.STOCK_DATABASE_NAME, config.COLLECTION_NAME_STOCK_BASIC_INFO)
stock_info_spyder.get_realtime_news()