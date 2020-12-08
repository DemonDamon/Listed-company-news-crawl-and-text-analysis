# 1. 爬取历史数据
from Gon.jrj_spyder import JrjSpyder
# 1.1 针对历史数据进行去重清洗


# 2. 抽取出新闻中所涉及的股票，并保存其股票代码在collection中新的一列
from Leorio.tokenization import Tokenization
# tokenization = Tokenization(import_module="jieba", user_dict="finance_dict.txt")
# tokenization.update_news_database_rows(config.DATABASE_NAME, "nbd_test")

# 3. 创建新的数据库，针对每一个股票，将所有涉及该股票的新闻都保存在新的数据库