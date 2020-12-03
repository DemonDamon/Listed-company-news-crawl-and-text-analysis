"""
中国证券网：https://www.cnstock.com
公司聚焦：https://company.cnstock.com/company/scp_gsxw
公告解读：https://ggjd.cnstock.com/gglist/search/qmtbbdj
公告快讯：https://ggjd.cnstock.com/gglist/search/ggkx
利好公告：https://ggjd.cnstock.com/company/scp_ggjd/tjd_sdlh
"""

import __init__
from spyder import Spyder

from Kite import config
from Kite import utils

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver


class CnStockSpyder(Spyder):

    def __init__(self):
        super(CnStockSpyder, self).__init__()
        self.col = self.db_obj.create_col(self.db, config.COLLECTION_NAME_CNSTOCK)
        self.driver = webdriver.Chrome(executable_path=config.CHROME_DRIVER)

    def get_url_info(self, url):
        respond = requests.get(url)
        respond.encoding = BeautifulSoup(respond.content, "lxml").original_encoding
        bs = BeautifulSoup(respond.text, "lxml")
        span_list = bs.find_all("span")
        part = bs.find_all("p")
        article = ""
        date = ""
        for span in span_list:
            if "class" in span.attrs and span["class"] == ["timer"]:
                date = span.text
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

        return date, article

    def get_historical_news(self, url):
        crawled_urls_list = self.extract_data(["Url"])[0]
        print("[INFO] history data length is {} ... ".format(len(crawled_urls_list)))
        self.driver.get(url)
        while True:
            more_btn = self.driver.find_element_by_id('j_more_btn')
            print("1-{}".format(more_btn.text))
            if more_btn.text == "加载更多":
                more_btn.click()
                time.sleep(random.random())  # sleep random time less 1s
            elif more_btn.text == "加载中...":
                time.sleep(random.random()+2)
                more_btn = self.driver.find_element_by_id('j_more_btn')
                print("2-{}".format(more_btn.text))
                if more_btn.text == "加载更多":
                    more_btn.click()
                else:
                    break
            else:
                more_btn.click()
                break
        bs = BeautifulSoup(self.driver.page_source, "html.parser")
        for li in bs.find_all("li", attrs={"class": ["newslist"]}):
            a = li.find_all("h2")[0].find("a")
            if a["href"] not in crawled_urls_list:
                print("[INFO] href not in history {}".format(a["href"]))
                date, article = self.get_url_info(a["href"])
                while article == "" and self.is_article_prob >= .1:
                    self.is_article_prob -= .1
                    date, article = self.get_url_info(a["href"])
                self.is_article_prob = .5
                if article != "":
                    data = {"Date": date,
                            "Url": a["href"],
                            "Title": a["title"],
                            "Article": article}
                    self.col.insert_one(data)


if __name__ == '__main__':
    cnstock_spyder = CnStockSpyder()
    for url_to_be_crawled in config.WEBSITES_LIST_TO_BE_CRAWLED_CNSTOCK:
        print("[INFO] start crawling {} ...".format(url_to_be_crawled))
        cnstock_spyder.get_historical_news(url_to_be_crawled)
        print("[INFO] finished ...")
        time.sleep(30)
    cnstock_spyder.driver.quit()

    # cnstock_spyder.get_historical_news("https://company.cnstock.com/company/scp_gsxw")
    # cnstock_spyder.get_historical_news("https://ggjd.cnstock.com/gglist/search/qmtbbdj")
    # cnstock_spyder.get_historical_news("https://ggjd.cnstock.com/gglist/search/ggkx")
    # cnstock_spyder.get_historical_news("https://ggjd.cnstock.com/company/scp_ggjd/tjd_sdlh")