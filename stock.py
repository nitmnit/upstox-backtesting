import glob
import json
import os
import time
from collections import OrderedDict

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import csv
# IS_HEADLESS = False
# NSE_URL = 'https://www.nseindia.com/products/content/equities/equities/eq_security.htm'
# chrome_options = Options()
# if IS_HEADLESS:
#     chrome_options.add_argument("--headless")
# chrome_options.add_argument('window-size=1920,1080')
# desired_capabilities = DesiredCapabilities.CHROME
# desired_capabilities['loggingPrefs'] = {"browser": "SEVERE"}
# driver = webdriver.Chrome(desired_capabilities=DesiredCapabilities.CHROME, chrome_options=chrome_options)
# wait_time = 3  # wait for elements to load
#
# symbol_name = 'SBIN'
# driver.get(NSE_URL)
# symbol = driver.find_element_by_id('symbol')
# series = driver.find_element_by_id('series')
# rdPeriod = driver.find_element_by_id('rdPeriod')
# dateRange = driver.find_element_by_id('dateRange')
# symbol.send_keys(symbol_name)
# driver.find_element_by_xpath('//*[@id="series"]/option[text()="EQ"]').click()
# rdPeriod.click()
# driver.find_element_by_xpath('//*[@id="dateRange"]/option[text()="1 Day"]').click()
# driver.find_element_by_id('get').click()
# time.sleep(1000)
#
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class SeleniumConnector(object):
    def __init__(self, is_headless=False, ):
        chrome_options = Options()
        if is_headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('window-size=1920,1080')
        # chrome_options.add_argument("download.default_directory=C:/Users/Administrator/PycharmProjects/Stock/downloads")
        prefs = {'download.default_directory': 'C:/Users/Administrator/PycharmProjects/Stock/downloads'}
        chrome_options.add_experimental_option('prefs', prefs)
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['loggingPrefs'] = {"browser": "SEVERE"}
        self.driver = webdriver.Chrome(desired_capabilities=DesiredCapabilities.CHROME, chrome_options=chrome_options)
        self.wait_time = 3


class DataDownloader(object):
    def __init__(self, index='NSE', ):
        self.NSE_URL = 'https://www.nseindia.com/products/content/equities/equities/eq_security.htm'
        self.index = 'NSE'
        self.sel = SeleniumConnector()

    def get_data_file(self, symbol, series='EQ', time_period='1 Day', ):
        if self.index == 'NSE':
            self.sel.driver.get(self.NSE_URL)
        else:
            raise Exception('Not available.')
        time_periods = ['1 Day', '7 Days', '1 month', '2 weeks', '1 month', '3 months', '365 Days', '24 Months', ]
        if time_period not in time_periods:
            raise Exception('Invalid time period.')
        self.wait_for_element(By.ID, 'symbol')
        symbol_element = self.sel.driver.find_element_by_id('symbol')
        # series = driver.find_element_by_id('series')
        self.sel.driver.find_element_by_id('rdPeriod').click()
        # dateRange = self.sel.driver.find_element_by_id('dateRange')
        symbol_element.send_keys(symbol)
        self.sel.driver.find_element_by_xpath('//*[@id="series"]/option[text()="' + series + '"]').click()
        self.sel.driver.find_element_by_xpath('//*[@id="dateRange"]/option[text()="' + time_period + '"]').click()
        self.sel.driver.find_element_by_id('get').click()
        try:
            self.wait_for_element(By.CSS_SELECTOR, '#historicalData > div.historic-bar > '
                                                   'span.download-data-link > a')
            self.sel.driver.find_element_by_css_selector('#historicalData > div.historic-bar > '
                                                         'span.download-data-link > a').click()
        except:
            pass

    def wait_for_element(self, selector_type, selector_value, timeout=10):
        try:
            WebDriverWait(self.sel.driver, timeout).until(
                expected_conditions.presence_of_element_located((selector_type, selector_value)))
        except TimeoutException:
            self.fail(msg="{} {} not found.".format(selector_type, selector_value))


NIFTY50 = ['ADANIPORTS', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL',
           'INFRATEL', 'CIPLA', 'COALINDIA', 'DRREDDY', 'EICHERMOT', 'GAIL', 'GRASIM', 'HCLTECH', 'HDFCBANK',
           'HEROMOTOCO', 'HINDALCO', 'HINDPETRO', 'HINDUNILVR', 'HDFC', 'ITC', 'ICICIBANK', 'IBULHSGFIN', 'IOC',
           'INDUSINDBK', 'INFY', 'KOTAKBANK', 'LT', 'LUPIN', 'M&M', 'MARUTI', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE',
           'SBIN', 'SUNPHARMA', 'TCS', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'UPL', 'ULTRACEMCO', 'VEDL',
           'WIPRO', 'YESBANK', 'ZEEL', ]

# data_downloader = DataDownloader()
# for symbol in NIFTY50:
#     data_downloader.get_data_file(symbol=symbol, time_period='365 Days')

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS = os.path.join(DIRECTORY, 'downloads')
data_files = sorted(glob.glob(DOWNLOADS.replace('\\', '/') + '/' + '*.csv'))

date_wise_change = OrderedDict()
for file in data_files:
    with open(file.replace('\\', '/')) as csv_reader:
        dict_reader = csv.DictReader(csv_reader)
        for line in dict_reader:
            if line['Date'] not in date_wise_change.keys():
                date_wise_change[line['Date']] = OrderedDict()
            date_wise_change[line['Date']][line['Symbol']] = (float(line['Open Price']) - float(
                line['Close Price'])) / float(line['Open Price'])

print(date_wise_change)
print('\n')
print('\n')
whole_minimum = []
for key, value in date_wise_change.iteritems():
    sorted_data = sorted(value.items(), key=lambda x:x[1])
    whole_minimum.append({key: sorted_data})
    # minimum = {'Change': None, 'Symbol': None, 'Date': None}
    # for symbol_name, change in value.iteritems():
    #     if not minimum['Change'] or minimum['Change'] > change:
    #         minimum['Change'] = change
    #         minimum['Symbol'] = symbol_name
    #         minimum['Date'] = key
    # whole_minimum.append(minimum)

print(json.dumps(whole_minimum))
# with open(os.path.join('data', 'equity_symbols.csv')) as csv_reader:
#     dict_reader = csv.DictReader(csv_reader)
#     data_downloader = DataDownloader()
#     for line in dict_reader:
#         data_downloader.get_data_file(symbol=line['SYMBOL'], time_period='365 Days')
