"""
每经网：http://www.nbd.com.cn
A股动态：http://stocks.nbd.com.cn/columns/275/page/1
"""

import __init__
from spyder import Spyder

from Kite.database import Database
from Kite import config
from Kite import utils

import re
import time
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class NbdSpyder(Spyder):

    def __init__(self, database_name, collection_name):
        super(NbdSpyder, self).__init__()
        self.db_obj = Database()
        self.col = self.db_obj.conn[database_name].get_collection(collection_name)
        self.terminated_amount = 0
        self.db_name = database_name
        self.col_name = collection_name

    def get_url_info(self, url):
        try:
            bs = utils.html_parser(url)
        except Exception:
            return False
        span_list = bs.find_all("span")
        part = bs.find_all("p")
        article = ""
        date = ""
        for span in span_list:
            if "class" in span.attrs and span.text and span["class"] == ["time"]:
                    string = span.text.split()
                    for dt in string:
                        if dt.find("-") != -1:
                            date += dt + " "
                        elif dt.find(":") != -1:
                            date += dt
                    break
        for paragraph in part:
            chn_status = utils.count_chn(str(paragraph))
            possible = chn_status[1]
            if possible > self.is_article_prob:
                article += str(paragraph)
        while article.find("<") != -1 and article.find(">") != -1:
            string = article[article.find("<"):article.find(">")+1]
            article = article.replace(string, "")
        while article.find("\u3000") != -1:
            article = article.replace("\u3000", "")
        article = " ".join(re.split(" +|\n+", article)).strip()

        return [date, article]

    def get_historical_news(self, start_page=684):
        date_list = self.db_obj.get_data(self.db_name, self.col_name, keys=["Date"])["Date"].to_list()
        if len(date_list) == 0:
            # 说明没有历史数据，从头开始爬取
            crawled_urls_list = []
            page_urls = ["{}/{}".format(config.WEBSITES_LIST_TO_BE_CRAWLED_NBD, page_id)
                         for page_id in range(start_page, 0, -1)]
            for page_url in page_urls:
                bs = utils.html_parser(page_url)
                a_list = bs.find_all("a")
                for a in a_list:
                    if "click-statistic" in a.attrs and a.string \
                            and a["click-statistic"].find("Article_") != -1 \
                            and a["href"].find("http://www.nbd.com.cn/articles/") != -1:
                        if a["href"] not in crawled_urls_list:
                            result = self.get_url_info(a["href"])
                            while not result:
                                self.terminated_amount += 1
                                if self.terminated_amount > config.NBD_MAX_REJECTED_AMOUNTS:
                                    # 始终无法爬取的URL保存起来
                                    with open(config.RECORD_NBD_FAILED_URL_TXT_FILE_PATH, "a+") as file:
                                        file.write("{}\n".format(a["href"]))
                                    logging.info("rejected by remote server longer than {} minutes, "
                                                 "and the failed url has been written in path {}"
                                                 .format(config.NBD_MAX_REJECTED_AMOUNTS,
                                                         config.RECORD_NBD_FAILED_URL_TXT_FILE_PATH))
                                    break
                                logging.info("rejected by remote server, request {} again after "
                                             "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                                time.sleep(60 * self.terminated_amount)
                                result = self.get_url_info(a["href"])
                            if not result:
                                # 爬取失败的情况
                                logging.info("[FAILED] {} {}".format(a.string, a["href"]))
                            else:
                                # 有返回但是article为null的情况
                                date, article = result
                                while article == "" and self.is_article_prob >= .1:
                                    self.is_article_prob -= .1
                                    result = self.get_url_info(a["href"])
                                    while not result:
                                        self.terminated_amount += 1
                                        if self.terminated_amount > config.NBD_MAX_REJECTED_AMOUNTS:
                                            # 始终无法爬取的URL保存起来
                                            with open(config.RECORD_NBD_FAILED_URL_TXT_FILE_PATH, "a+") as file:
                                                file.write("{}\n".format(a["href"]))
                                            logging.info("rejected by remote server longer than {} minutes, "
                                                         "and the failed url has been written in path {}"
                                                         .format(config.NBD_MAX_REJECTED_AMOUNTS,
                                                                 config.RECORD_NBD_FAILED_URL_TXT_FILE_PATH))
                                            break
                                        logging.info("rejected by remote server, request {} again after "
                                                     "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                                        time.sleep(60 * self.terminated_amount)
                                        result = self.get_url_info(a["href"])
                                    date, article = result
                                self.is_article_prob = .5
                                if article != "":
                                    data = {"Date": date,
                                            # "PageId": page_url.split("/")[-1],
                                            "Url": a["href"],
                                            "Title": a.string,
                                            "Article": article}
                                    # self.col.insert_one(data)
                                    self.db_obj.insert_data(self.db_name, self.col_name, data)
                                    logging.info("[SUCCESS] {} {} {}".format(date, a.string, a["href"]))
        else:
            is_stop = False
            start_date = max(date_list)
            page_start_id = 1
            while not is_stop:
                page_url = "{}/{}".format(config.WEBSITES_LIST_TO_BE_CRAWLED_NBD, page_start_id)
                bs = utils.html_parser(page_url)
                a_list = bs.find_all("a")
                for a in a_list:
                    if "click-statistic" in a.attrs and a.string \
                            and a["click-statistic"].find("Article_") != -1 \
                            and a["href"].find("http://www.nbd.com.cn/articles/") != -1:
                        result = self.get_url_info(a["href"])
                        while not result:
                            self.terminated_amount += 1
                            if self.terminated_amount > config.NBD_MAX_REJECTED_AMOUNTS:
                                # 始终无法爬取的URL保存起来
                                with open(config.RECORD_NBD_FAILED_URL_TXT_FILE_PATH, "a+") as file:
                                    file.write("{}\n".format(a["href"]))
                                logging.info("rejected by remote server longer than {} minutes, "
                                             "and the failed url has been written in path {}"
                                             .format(config.NBD_MAX_REJECTED_AMOUNTS,
                                                     config.RECORD_NBD_FAILED_URL_TXT_FILE_PATH))
                                break
                            logging.info("rejected by remote server, request {} again after "
                                         "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                            time.sleep(60 * self.terminated_amount)
                            result = self.get_url_info(a["href"])
                        if not result:
                            # 爬取失败的情况
                            logging.info("[FAILED] {} {}".format(a.string, a["href"]))
                        else:
                            # 有返回但是article为null的情况
                            date, article = result
                            if date > start_date:
                                while article == "" and self.is_article_prob >= .1:
                                    self.is_article_prob -= .1
                                    result = self.get_url_info(a["href"])
                                    while not result:
                                        self.terminated_amount += 1
                                        if self.terminated_amount > config.NBD_MAX_REJECTED_AMOUNTS:
                                            # 始终无法爬取的URL保存起来
                                            with open(config.RECORD_NBD_FAILED_URL_TXT_FILE_PATH, "a+") as file:
                                                file.write("{}\n".format(a["href"]))
                                            logging.info("rejected by remote server longer than {} minutes, "
                                                         "and the failed url has been written in path {}"
                                                         .format(config.NBD_MAX_REJECTED_AMOUNTS,
                                                                 config.RECORD_NBD_FAILED_URL_TXT_FILE_PATH))
                                            break
                                        logging.info("rejected by remote server, request {} again after "
                                                     "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                                        time.sleep(60 * self.terminated_amount)
                                        result = self.get_url_info(a["href"])
                                    date, article = result
                                self.is_article_prob = .5
                                if article != "":
                                    data = {"Date": date,
                                            "Url": a["href"],
                                            "Title": a.string,
                                            "Article": article}
                                    self.db_obj.insert_data(self.db_name, self.col_name, data)
                                    logging.info("[SUCCESS] {} {} {}".format(date, a.string, a["href"]))
                            else:
                                is_stop = True
                                break
                if not is_stop:
                    page_start_id += 1

    def get_realtime_news(self, url):
        pass


# """
# Example-1:
# 爬取历史新闻数据
# """
# if __name__ == "__main__":
#     nbd_spyder = NbdSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_NBD)
#     nbd_spyder.get_historical_news(start_page684)
#
#     # TODO：继续爬取RECORD_NBD_FAILED_URL_TXT_FILE_PATH文件中失败的URL
#     pass


"""
Example-2:
爬取实时新闻数据
"""
if __name__ == '__main__':
    from Kite.database import Database
    from Kite import config
    import threading

    # 如果没有历史数据从头爬取，如果已爬取历史数据，则从最新的时间开始爬取
    # 如历史数据中最近的新闻时间是"2020-12-09 20:37:10"，则从该时间开始爬取
    nbd_spyder = NbdSpyder(config.DATABASE_NAME, config.COLLECTION_NAME_NBD)
    nbd_spyder.get_historical_news()