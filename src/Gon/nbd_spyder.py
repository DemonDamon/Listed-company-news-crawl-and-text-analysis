"""
每经网：http://www.nbd.com.cn
A股动态：http://stocks.nbd.com.cn/columns/275/page/1
"""

import __init__
from spyder import Spyder

from Kite import config
from Kite import utils

import re
import os
import time
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class NbdSpyder(Spyder):

    def __init__(self):
        super(NbdSpyder, self).__init__()
        self.col = self.db_obj.create_col(self.db, config.COLLECTION_NAME_NBD)
        self.terminated_amount = 0

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

    def get_historical_news(self, start_page):
        if len(self.extract_data(["PageId"])[0]) != 0:
            latest_page_id = min(self.extract_data(["PageId"])[0])
        else:
            latest_page_id = start_page
        crawled_urls_list = list()
        for page_id in range(start_page, int(latest_page_id)-1, -1):
            query_results = self.query_news("PageId", page_id)
            for qr in query_results:
                crawled_urls_list.append(qr["Url"])
        # crawled_urls_list = self.extract_data(["Url"])[0]  # abandoned
        logging.info("[INFO] the length of crawled data in {} is {} ... ".format(start_page, len(crawled_urls_list)))

        page_urls = ["{}/{}".format(config.WEBSITES_LIST_TO_BE_CRAWLED_NBD, page_id) for page_id in range(start_page, 0, -1)]
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
                                with open(config.RECORD_NBD_START_PAGE_TXT_FILE_PATH, "w") as file:
                                    file.write(page_url.split("/")[-1])
                                raise Exception("rejected by remote server longer than {} minutes ... "
                                                .format(config.NBD_MAX_REJECTED_AMOUNTS))
                            logging.info("[INFO] rejected by remote server, request {} again after "
                                         "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                            time.sleep(60 * self.terminated_amount)
                            result = self.get_url_info(a["href"])
                        date, article = result
                        while article == "" and self.is_article_prob >= .1:
                            self.is_article_prob -= .1
                            result = self.get_url_info(a["href"])
                            while not result:
                                self.terminated_amount += 1
                                if self.terminated_amount > config.NBD_MAX_REJECTED_AMOUNTS:
                                    with open(config.RECORD_NBD_START_PAGE_TXT_FILE_PATH, "w") as file:
                                        file.write(page_url.split("/")[-1])
                                    raise Exception("rejected by remote server longer than {} minutes ... "
                                                    .format(config.NBD_MAX_REJECTED_AMOUNTS))
                                logging.info("[INFO] rejected by remote server, request {} again after "
                                             "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                                time.sleep(60 * self.terminated_amount)
                                result = self.get_url_info(a["href"])
                            article_specific_date, article = result
                        self.is_article_prob = .5
                        if article != "":
                            data = {"Date": date,
                                    "PageId": page_url.split("/")[-1],
                                    "Url": a["href"],
                                    "Title": a.string,
                                    "Article": article}
                            self.col.insert_one(data)
                            logging.info("{} {} \n{}".format(date, a.string, a["href"]))

    def get_realtime_news(self, url):
        pass


if __name__ is "__main__":
    nbd_spyder = NbdSpyder()
    if not os.path.exists(config.RECORD_NBD_START_PAGE_TXT_FILE_PATH):
        nbd_spyder.get_historical_news(684)
    else:
        with open(config.RECORD_NBD_START_PAGE_TXT_FILE_PATH, "r") as f:
            start_page = f.read()
        nbd_spyder.get_historical_news(start_page)
