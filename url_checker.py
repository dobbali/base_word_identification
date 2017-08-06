
import logging
from googleads import adwords
import time
import urllib.request
from random import randint
import warnings
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Pool
import pandas as pd
from bs4 import BeautifulSoup, Comment
import requests
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class UrlCheck():
    """
    Takes list of urls and gives if the url is returning any results or not

    Attributes
    ----------
    report_type : list
        list with urls
    """

    def __init__(self):


        self.USER_AGENT = 'User-agent'
        self.ACCEPT = 'Accept'
        self.ACCEPT_ENCODING = 'Accept-Encoding'
        self.ACCEPT_LANGUAGE = 'Accept-language'
        self.CONNECTION = 'Connection'

        self.CONNECTION_DEFAULT = "keep-alive"
        self.ACCEPT_ENCODING_DEFAULT = "utf-8"
        self.ACCEPT_LANGUAGE_DEFAULT = 'en-us,en;q=0.5'

        self.USER_AGENT_MAC_FIREFOX = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/45.0.2"

        self.HEADER_FIREFOX_MAC = {self.USER_AGENT: self.USER_AGENT_MAC_FIREFOX,
            self.ACCEPT: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                self.ACCEPT_ENCODING: self.ACCEPT_ENCODING_DEFAULT,
                   self.ACCEPT_LANGUAGE: self.ACCEPT_LANGUAGE_DEFAULT,
                        self.CONNECTION: self.CONNECTION_DEFAULT}

        self.HEADER_CHROME_WINDOWS = {self.USER_AGENT: "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
            self.ACCEPT: "application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
                self.ACCEPT_ENCODING: self.ACCEPT_ENCODING_DEFAULT,
                    self.ACCEPT_LANGUAGE: self.ACCEPT_LANGUAGE_DEFAULT,
                        self.CONNECTION: self.CONNECTION_DEFAULT}

        self.USER_HEADERS = [self.HEADER_FIREFOX_MAC, self.HEADER_CHROME_WINDOWS]


    def map_results(self, result_dict, main_df):
        main_df['Results'] = main_df['FinalURL'].map(result_dict)
        return main_df

    def run(self, url_list):
        """
        Multi processing/Multi threading is carried out

        """

        start = time.ctime()
        print(start)
        pT = ThreadPool(128)
        results = pT.map_async(self.get_request, url_list)
        pT.close()
        pT.join()

        all_req = []
        for i in results.get():
            all_req.append(i)

        pP = Pool(10)
        results = pP.map_async(self.get_count, all_req)
        pP.close()
        pP.join()

        counts = []
        for i in results.get():
            counts.append(i)

        result_df = pd.DataFrame({"FinalURL":url_list,"Results":counts})
        result_dict = dict(zip(result_df.FinalURL, result_df.Results))
        end = time.ctime()
        print(end)
        return  result_dict


    # Random User-Agent string
    def get_random_header(self):
        return self.USER_HEADERS[randint(0,(len(self.USER_HEADERS)-1))]

    # Opener with random header settings
    def get_random_opener(self):
        opener = urllib.request.build_opener()
        randomHeader = self.get_random_header()
        opener.addheaders = [(self.USER_AGENT,randomHeader[self.USER_AGENT]),
                             (self.ACCEPT,randomHeader[self.ACCEPT])
                             ,(self.ACCEPT_ENCODING,randomHeader[self.ACCEPT_ENCODING])
                             , (self.ACCEPT_LANGUAGE, randomHeader[self.ACCEPT_LANGUAGE])
                             ,(self.CONNECTION,randomHeader[self.CONNECTION])
                             ]
        return opener

    def get_request(self, url):
        try:
            resp= requests.get(url, self.get_random_header())
        except Exception as e:
            print(e)
            resp = "failed"
        return resp

    def get_count(self, resp):
        """
        Takes url as input and returns number of results display on the page.

        Parameters
        ----------
        url : str
            url that needs to be checked if working or not
        delay_min : int
            minimum time between consecutive checks
        deplay_max : int
            maximum time between consecutive checks
        """

        # time.sleep(random.uniform(delay_min, delay_max))
        try:
            if resp.status_code == 404:
                count = 0
                return count
            soup = BeautifulSoup(resp.text, 'lxml')
            soup_string = str(soup)
            if 'We’re Sorry.' in soup_string:
                return 0

            comments = soup.findAll(text=lambda text: isinstance(text, Comment))
            comments = [item.strip() for item in comments]
            pat = re.compile("product result count: ([0-9]+)")
            new_list = [i for i in comments if pat.match(i)]
            count = re.findall("([0-9]+)", str(new_list))
            count = count[0]
        except Exception as e:
            print(e)
            print(resp)
            count = "re check"
        return  count
