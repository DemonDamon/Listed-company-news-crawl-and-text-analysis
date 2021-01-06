from Kite import config
from Gon.jrjspyder import JrjSpyder


jrj_spyder = JrjSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_JRJ)
jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ)  # 补充爬虫数据到最新日期
jrj_spyder.get_realtime_news()