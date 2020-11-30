import __init__

from Kite.database import Database
from Kite import config
from Kite import utils

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver


class CnStockSpyder(object):

    def __init__(self):
        db_obj = Database()
        db = db_obj.create_db(config.DATABASE_NAME_CNSTOCK)
        self.col = db_obj.create_col(db, config.COLLECTION_NAME_CNSTOCK)
        self.is_article_prob = .5
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

    def extract_data(self, tag_list):
        data = list()
        for tag in tag_list:
            exec(tag + " = self.col.distinct('" + tag + "')")
            exec("data.append(" + tag + ")")
        return data

    def get_historical_news_by_selenium(self, url):
        crawled_urls_list = self.extract_data(["Url"])[0]
        self.driver.get(url)
        while True:
            more_btn = self.driver.find_element_by_id('j_more_btn')
            if more_btn.text == "加载更多":
                more_btn.click()
                time.sleep(random.random())  # sleep random time less 1s
            else:
                break
        bs = BeautifulSoup(self.driver.page_source, "html.parser")
        for li in bs.find_all("li", attrs={"class": ["newslist"]}):
            a = li.find_all("h2")[0].find("a")
            if a["href"] not in crawled_urls_list:
                date, article = self.get_url_info(a["href"])
                while article == '' and self.is_article_prob >= .1:
                    self.is_article_prob -= .1
                    date, article = self.get_url_info(a['href'])
                self.is_article_prob = .5
                if article != '':
                    data = {'Date': date,
                            'Url': a['href'],
                            'Title': a['title'],
                            'Article': article}
                    self.col.insert_one(data)
        self.driver.quit()


if __name__ == '__main__':
    cnstock_spyder = CnStockSpyder()
    # cnstock_spyder.get_historical_news_by_selenium("https://company.cnstock.com/company/scp_gsxw")
    # cnstock_spyder.get_historical_news_by_selenium("https://ggjd.cnstock.com/gglist/search/qmtbbdj")
    # cnstock_spyder.get_historical_news_by_selenium("https://ggjd.cnstock.com/gglist/search/ggkx")
    cnstock_spyder.get_historical_news_by_selenium("https://ggjd.cnstock.com/company/scp_ggjd/tjd_sdlh")