MONGODB_IP = 'localhost'
MONGODB_PORT = 27017
THREAD_NUMS_FOR_SPYDER = 4

DATABASE_NAME = 'finnewshunter'

COLLECTION_NAME_CNSTOCK = 'cnstock'
CHROME_DRIVER = 'D:\\anaconda3\\chromedriver.exe'
# WEBSITES_LIST_TO_BE_CRAWLED_CNSTOCK = {'https://company.cnstock.com/company/scp_gsxw': "公司聚焦",
#                                        'https://ggjd.cnstock.com/gglist/search/qmtbbdj': "公告解读",
#                                        'https://ggjd.cnstock.com/gglist/search/ggkx': "公告快讯",
#                                        'https://ggjd.cnstock.com/company/scp_ggjd/tjd_sdlh': "利好公告"}
WEBSITES_LIST_TO_BE_CRAWLED_CNSTOCK = {'https://company.cnstock.com/company/scp_gsxw': "公司聚焦",
                                       'http://ggjd.cnstock.com/company/scp_ggjd/tjd_bbdj': "公告解读",
                                       'http://ggjd.cnstock.com/company/scp_ggjd/tjd_ggkx': "公告快讯",
                                       'https://ggjd.cnstock.com/company/scp_ggjd/tjd_sdlh': "利好公告"}
RECORD_CNSTOCK_FAILED_URL_TXT_FILE_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Gon\\cnstock_failed_urls.txt"
CNSTOCK_MAX_REJECTED_AMOUNTS = 10

COLLECTION_NAME_JRJ = 'jrj'
JRJ_DATE_RANGE = 100
WEBSITES_LIST_TO_BE_CRAWLED_JRJ = "http://stock.jrj.com.cn/xwk"
RECORD_JRJ_FAILED_URL_TXT_FILE_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Gon\\jrj_failed_urls.txt"
JRJ_MAX_REJECTED_AMOUNTS = 10

COLLECTION_NAME_NBD = 'nbd'
WEBSITES_LIST_TO_BE_CRAWLED_NBD = 'http://stocks.nbd.com.cn/columns/275/page'
RECORD_NBD_FAILED_URL_TXT_FILE_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Gon\\nbd_failed_urls.txt"
NBD_TOTAL_PAGES_NUM = 684
NBD_MAX_REJECTED_AMOUNTS = 10

TUSHARE_TOKEN = "97fbc4c73727b5d171ca6670cbc4af8b0a3de5fbab74b52f30b598cc"
STOCK_DATABASE_NAME = 'stock'
COLLECTION_NAME_STOCK_BASIC_INFO = "basic_info"
STOCK_DAILY_EXCEPTION_TXT_FILE_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Gon\\start_stock_code.txt"

ALL_NEWS_OF_SPECIFIC_STOCK_DATABASE = "stocknews"

TOPIC_NUMBER = 200
SMV_TUNED_PARAMTERS = {"kernel": ["rbf"], "gamma": [10, 20, 50, 100, 150, 200], "C": [10, 15, 20, 30, 50, 100]}
RDFOREST_TUNED_PARAMTERS = {'n_estimators': [1, 2, 3, 4, 5, 10],
                            'criterion': ['gini', 'entropy'],
                            'max_features': ['auto', 'sqrt']}
CLASSIFIER_SCORE_LIST = ["f1_weighted"]
USER_DEFINED_DICT_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Leorio\\financedict.txt"
CHN_STOP_WORDS_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Leorio\\chnstopwords.txt"