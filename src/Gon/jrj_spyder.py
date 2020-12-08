"""
金融界：http://www.jrj.com.cn
股票频道全部新闻：http://stock.jrj.com.cn/xwk/202012/20201203_1.shtml
"""

import __init__
from spyder import Spyder

from Kite.database import Database
from Kite import config
from Kite import utils

import time
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class JrjSpyder(Spyder):

    def __init__(self, database_name, collection_name):
        super(JrjSpyder, self).__init__()
        self.db_obj = Database()
        self.col = self.db_obj.conn[database_name].get_collection(collection_name)
        self.terminated_amount = 0
        self.db_name = database_name
        self.col_name = collection_name

    def get_url_info(self, url, specific_date):
        try:
            bs = utils.html_parser(url)
        except Exception:
            return False
        date = ""
        for span in bs.find_all("span"):
            if span.contents[0] == "jrj_final_date_start":
                date = span.text.replace("\r", "").replace("\n", "")
                break
        if date == "":
            date = specific_date
        article = ""
        for p in bs.find_all("p"):
            if not p.find_all("jrj_final_daohang_start") and p.attrs == {} and \
                    not p.find_all("input") and not p.find_all("a", attrs={"class": "red"}) and not p.find_all("i") and not p.find_all("span"):
            # if p.contents[0] != "jrj_final_daohang_start1" and p.attrs == {} and \
            #         not p.find_all("input") and not p.find_all("a", attrs={"class": "red"}) and not p.find_all("i"):
                article += p.text.replace("\r", "").replace("\n", "").replace("\u3000", "")

        return [date, article]

    def get_historical_news(self, url, start_date, end_date):
        # # 抽取数据库中已爬取的从start_date到latest_date_str所有新闻，避免重复爬取
        # # 比如数据断断续续爬到了2016-10-10 15:00:00时间节点，但是在没调整参数的情
        # # 况下，从2015-01-01(自己设定)开始重跑程序会导致大量重复数据，因此在这里稍
        # # 作去重。直接从最新的时间节点开始跑是完全没问题，但从2015-01-01(自己设定)
        # # 开始重跑程序可以尝试将前面未成功爬取的URL重新再试一遍
        # extracted_data_list = self.extract_data(["Date"])[0]
        # if len(extracted_data_list) != 0:
        #     latest_date_str = max(extracted_data_list).split(" ")[0]
        # else:
        #     latest_date_str = start_date
        # logging.info("latest time in database is {} ... ".format(latest_date_str))
        # crawled_urls_list = list()
        # for _date in utils.get_date_list_from_range(start_date, latest_date_str):
        #     query_results = self.query_news("Date", _date)
        #     for qr in query_results:
        #         crawled_urls_list.append(qr["Url"])
        # # crawled_urls_list = self.extract_data(["Url"])[0]  # abandoned
        # logging.info("the length of crawled data from {} to {} is {} ... ".format(start_date,
        #                                                                           latest_date_str,
        #                                                                           len(crawled_urls_list)))

        crawled_urls_list = []
        dates_list = utils.get_date_list_from_range(start_date, end_date)
        dates_separated_into_ranges_list = utils.gen_dates_list(dates_list, config.JRJ_DATE_RANGE)

        for dates_range in dates_separated_into_ranges_list:
            for date in dates_range:
                first_url = "{}/{}/{}_1.shtml".format(url, date.replace("-", "")[0:6], date.replace("-", ""))
                max_pages_num = utils.search_max_pages_num(first_url, date)
                for num in range(1, max_pages_num + 1):
                    _url = "{}/{}/{}_{}.shtml".format(url, date.replace("-", "")[0:6], date.replace("-", ""), str(num))
                    bs = utils.html_parser(_url)
                    a_list = bs.find_all("a")
                    for a in a_list:
                        if "href" in a.attrs and a.string and \
                                a["href"].find("/{}/{}/".format(date.replace("-", "")[:4],
                                                                date.replace("-", "")[4:6])) != -1:
                            if a["href"] not in crawled_urls_list:
                                # 如果标题不包含"收盘","报于"等字样，即可写入数据库，因为包含这些字样标题的新闻多为机器自动生成
                                if a.string.find("收盘") == -1 and a.string.find("报于") == -1 and \
                                        a.string.find("新三板挂牌上市") == -1:
                                    result = self.get_url_info(a["href"], date)
                                    while not result:
                                        self.terminated_amount += 1
                                        if self.terminated_amount > config.JRJ_MAX_REJECTED_AMOUNTS:
                                            # 始终无法爬取的URL保存起来
                                            with open(config.RECORD_JRJ_FAILED_URL_TXT_FILE_PATH, "a+") as file:
                                                file.write("{}\n".format(a["href"]))
                                            logging.info("rejected by remote server longer than {} minutes, "
                                                         "and the failed url has been written in path {}"
                                                         .format(config.JRJ_MAX_REJECTED_AMOUNTS,
                                                                 config.RECORD_JRJ_FAILED_URL_TXT_FILE_PATH))
                                            break
                                        logging.info("rejected by remote server, request {} again after "
                                                     "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                                        time.sleep(60 * self.terminated_amount)
                                        result = self.get_url_info(a["href"], date)
                                    if not result:
                                        # 爬取失败的情况
                                        logging.info("[FAILED] {} {}".format(a.string, a["href"]))
                                    else:
                                        # 有返回但是article为null的情况
                                        article_specific_date, article = result
                                        while article == "" and self.is_article_prob >= .1:
                                            self.is_article_prob -= .1
                                            result = self.get_url_info(a["href"], date)
                                            while not result:
                                                self.terminated_amount += 1
                                                if self.terminated_amount > config.JRJ_MAX_REJECTED_AMOUNTS:
                                                    # 始终无法爬取的URL保存起来
                                                    with open(config.RECORD_JRJ_FAILED_URL_TXT_FILE_PATH, "a+") as file:
                                                        file.write("{}\n".format(a["href"]))
                                                    logging.info("rejected by remote server longer than {} minutes, "
                                                                 "and the failed url has been written in path {}"
                                                                 .format(config.JRJ_MAX_REJECTED_AMOUNTS,
                                                                         config.RECORD_JRJ_FAILED_URL_TXT_FILE_PATH))
                                                    break
                                                logging.info("rejected by remote server, request {} again after "
                                                             "{} seconds...".format(a["href"],
                                                                                    60 * self.terminated_amount))
                                                time.sleep(60 * self.terminated_amount)
                                                result = self.get_url_info(a["href"], date)
                                            article_specific_date, article = result
                                        self.is_article_prob = .5
                                        if article != "":
                                                data = {"Date": article_specific_date,
                                                        "Url": a["href"],
                                                        "Title": a.string,
                                                        "Article": article}
                                                # self.col.insert_one(data)
                                                self.db_obj.insert_data(self.db_name, self.col_name, data)
                                                logging.info("[SUCCESS] {} {} {}".format(article_specific_date,
                                                                                         a.string,
                                                                                         a["href"]))
                                    self.terminated_amount = 0  # 爬取结束后重置该参数
                                else:
                                    logging.info("[QUIT] {}".format(a.string))

    def get_realtime_news(self, url):
        pass


if __name__ == "__main__":
    jrj_spyder = JrjSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_JRJ)
    jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, "2020-12-04", "2020-12-08")
    # jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, "2020-07-06", "2020-12-08")
    # jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, "2018-04-03", "2020-12-06")
    # jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, "2018-01-02", "2020-12-03")
    # jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, "2017-07-18", "2018-01-01")
    # jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, "2016-04-15", "2020-12-03")

    # TODO：继续爬取RECORD_JRJ_FAILED_URL_TXT_FILE_PATH文件中失败的URL
    pass