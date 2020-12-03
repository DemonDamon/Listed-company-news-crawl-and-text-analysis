"""
金融界：http://www.jrj.com.cn
股票频道全部新闻：http://stock.jrj.com.cn/xwk/202012/20201203_1.shtml
"""

import __init__
from spyder import Spyder

from Kite import config
from Kite import utils
import logging

import re
import os
import time
import random
import requests
import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class JrjSpyder(Spyder):

    def __init__(self):
        super(JrjSpyder, self).__init__()
        self.col = self.db_obj.create_col(self.db, config.COLLECTION_NAME_JRJ)
        self.terminated_amount = 0

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
        # 抽取数据库中已爬取的从start_date到latest_date_str所有新闻，避免重复爬取
        extracted_data_list = self.extract_data(["Date"])[0]
        if len(extracted_data_list) != 0:
            latest_date_str = max(extracted_data_list).split(" ")[0]
        else:
            latest_date_str = start_date
        logging.info("latest time in database is {} ... ".format(latest_date_str))
        crawled_urls_list = list()
        for _date in utils.get_date_list_from_range(start_date, latest_date_str):
            query_results = self.query_news("Date", _date)
            for qr in query_results:
                crawled_urls_list.append(qr["Url"])
        # crawled_urls_list = self.extract_data(["Url"])[0]  # abandoned
        logging.info("the length of crawled data from {} to {} is {} ... ".format(start_date,
                                                                                         latest_date_str,
                                                                                         len(crawled_urls_list)))

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
                                # 如果标题不包含"快讯","收盘","报于"等字样，即保存，因为包含这些字样标题的新闻多为机器自动生成
                                if a.string.find("快讯") == -1 and \
                                        a.string.find("收盘") == -1 and a.string.find("报于") == -1:
                                    result = self.get_url_info(a["href"], date)
                                    while not result:
                                        self.terminated_amount += 1
                                        if self.terminated_amount > config.JRJ_MAX_REJECTED_AMOUNTS:
                                            with open(config.RECORD_JRJ_START_DATE_TXT_FILE_PATH, "w") as file:
                                                file.write(date)
                                            raise Exception("rejected by remote server longer than {} minutes ... "
                                                            .format(config.JRJ_MAX_REJECTED_AMOUNTS))
                                        logging.info("rejected by remote server, request {} again after "
                                                     "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                                        time.sleep(60 * self.terminated_amount)
                                        result = self.get_url_info(a["href"], date)
                                    article_specific_date, article = result
                                    while article == "" and self.is_article_prob >= .1:
                                        self.is_article_prob -= .1
                                        result = self.get_url_info(a["href"], date)
                                        while not result:
                                            self.terminated_amount += 1
                                            if self.terminated_amount > config.JRJ_MAX_REJECTED_AMOUNTS:
                                                with open(config.RECORD_JRJ_START_DATE_TXT_FILE_PATH, "w") as file:
                                                    file.write(date)
                                                raise Exception("rejected by remote server longer than {} minutes ... "
                                                                .format(config.JRJ_MAX_REJECTED_AMOUNTS))
                                            logging.info("rejected by remote server, request {} again after "
                                                         "{} seconds...".format(a["href"], 60 * self.terminated_amount))
                                            time.sleep(60 * self.terminated_amount)
                                            result = self.get_url_info(a["href"], date)
                                        article_specific_date, article = result
                                    self.is_article_prob = .5
                                    if article != "":
                                            data = {"Date": article_specific_date,
                                                    "Url": a["href"],
                                                    "Title": a.string,
                                                    "Article": article}
                                            self.col.insert_one(data)
                                            logging.info("[SUCCESS] {} {} {}".format(article_specific_date, a.string, a["href"]))
                                else:
                                    logging.info("[QUIT] {}".format(a.string))

    def get_realtime_news(self, url):
        pass


if __name__ == "__main__":
    jrj_spyder = JrjSpyder()
    if not os.path.exists(config.RECORD_JRJ_START_DATE_TXT_FILE_PATH):
        jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, "2016-02-01", "2020-12-03")
    else:
        with open(config.RECORD_JRJ_START_DATE_TXT_FILE_PATH, "r") as f:
            start_date = f.read()
        jrj_spyder.get_historical_news(config.WEBSITES_LIST_TO_BE_CRAWLED_JRJ, start_date, "2020-12-03")
