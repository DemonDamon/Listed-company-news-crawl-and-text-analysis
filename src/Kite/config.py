MONGODB_IP = 'localhost'
MONGODB_PORT = 27017
THREAD_NUMS_FOR_SPYDER = 4

DATABASE_NAME = 'finnewshunter'

COLLECTION_NAME_CNSTOCK = 'cnstock_test'
CHROME_DRIVER = 'D:\\anaconda3\\chromedriver.exe'
WEBSITES_LIST_TO_BE_CRAWLED_CNSTOCK = ['https://company.cnstock.com/company/scp_gsxw',
                                       'https://ggjd.cnstock.com/gglist/search/qmtbbdj',
                                       'https://ggjd.cnstock.com/gglist/search/ggkx',
                                       'https://ggjd.cnstock.com/company/scp_ggjd/tjd_sdlh']
RECORD_CNSTOCK_FAILED_URL_TXT_FILE_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Gon\\cnstock_crawl_failed_urls.txt"
CNSTOCK_MAX_REJECTED_AMOUNTS = 10

COLLECTION_NAME_JRJ = 'jrj'
JRJ_DATE_RANGE = 100
WEBSITES_LIST_TO_BE_CRAWLED_JRJ = "http://stock.jrj.com.cn/xwk"
RECORD_JRJ_START_DATE_TXT_FILE_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Gon\\jrj_start_date.txt"
JRJ_MAX_REJECTED_AMOUNTS = 10

COLLECTION_NAME_NBD = 'nbd'
WEBSITES_LIST_TO_BE_CRAWLED_NBD = 'http://stocks.nbd.com.cn/columns/275/page'
RECORD_NBD_START_PAGE_TXT_FILE_PATH = "D:\\workfiles\\gpu私有云代码备份\\Listed-company-news-crawl-and-text-analysis\\src\\Gon\\nbd_start_page.txt"
NBD_TOTAL_PAGES_NUM = 684
NBD_MAX_REJECTED_AMOUNTS = 10
