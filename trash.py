import logging
import time
import urlparse
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import psycopg2
import requests
from kiteconnect import KiteConnect, KiteTicker

from webpage_interaction import SeleniumConnector


class ZerodhaConnector(object):
    API_KEY = 'd16w0nfo5y5bqvku'
    API_SECRET = 'ifwiilkg59aluasen3t0rb1tzv7iofoy'
    BASE_URL = 'https://api.kite.trade'
    HISTORY = '/instruments/historical/'
    USERNAME = 'ZE7848'
    PASSWORD = 'lFf7PRwvJFf4'
    DEBUG = True
    DATABASE = {
        'NAME': 'stocks',
        'USERNAME': 'smartcity',
        'PASSWORD': 'smartcity',
        'HOST': 'localhost',
    }
    NIFTY50 = ['ADANIPORTS', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL',
               'INFRATEL', 'CIPLA', 'COALINDIA', 'DRREDDY', 'EICHERMOT', 'GAIL', 'GRASIM', 'HCLTECH', 'HDFCBANK',
               'HEROMOTOCO', 'HINDALCO', 'HINDPETRO', 'HINDUNILVR', 'HDFC', 'ITC', 'ICICIBANK', 'IBULHSGFIN', 'IOC',
               'INDUSINDBK', 'INFY', 'KOTAKBANK', 'LT', 'LUPIN', 'M&M', 'MARUTI', 'NTPC', 'ONGC', 'POWERGRID',
               'RELIANCE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'UPL', 'ULTRACEMCO',
               'VEDL', 'WIPRO', 'YESBANK', 'ZEEL', ]

    conn = psycopg2.connect(host="localhost", database=DATABASE['NAME'], user=DATABASE['USERNAME'],
                            password=DATABASE['PASSWORD'])

    def __init__(self):
        self.kite_connect = KiteConnect(api_key=self.API_KEY)
        self.request_token = self.get_request_token()
        self.kite_connect = KiteConnect(api_key=self.API_KEY)
        data = self.kite_connect.generate_session(self.request_token, api_secret=self.API_SECRET)
        self.access_token = data["access_token"]
        self.kite_connect.set_access_token(data["access_token"])
        self.kite_ticker = KiteTicker(api_key=self.API_KEY, access_token=self.access_token)

    @staticmethod
    def get_answer(question):
        if 'career' in question:
            answer = 'ims'
        elif 'watch' in question:
            answer = 'timex'
        elif 'mobile' in question:
            answer = 'sony'
        elif 'birth' in question:
            answer = 'dungarpur'
        elif 'shoe' in question:
            answer = '11'
        else:
            raise Exception('No answer found.')
        return answer

    def get_request_token(self):
        con = SeleniumConnector()
        con.driver.get(self.kite_connect.login_url())
        time.sleep(3)
        username_input = con.driver.find_element_by_css_selector('input[type="text"]')
        password_input = con.driver.find_element_by_css_selector('input[type="password"]')
        submit_button = con.driver.find_element_by_css_selector('button[type="submit"]')
        username_input.send_keys(self.USERNAME)
        password_input.send_keys(self.PASSWORD)
        submit_button.click()
        time.sleep(5)
        sq1_el = con.driver.find_element_by_css_selector('.twofa-form > div:nth-child(2) input')
        sq2_el = con.driver.find_element_by_css_selector('.twofa-form > div:nth-child(3) input')
        question1 = sq1_el.get_attribute('label')
        question2 = sq2_el.get_attribute('label')
        answer1 = self.get_answer(question1)
        answer2 = self.get_answer(question2)
        sq1_el.send_keys(answer1)
        sq2_el.send_keys(answer2)
        answer_submit_button = con.driver.find_element_by_css_selector('button[type="submit"]')
        answer_submit_button.click()
        time.sleep(3)
        parsed = urlparse.urlparse(con.driver.current_url)
        request_token = urlparse.parse_qs(parsed.query)['request_token'][0]
        con.driver.close()
        return request_token

    def get_intraday_data(self, instrument, date):
        resp = requests.get(self.BASE_URL + self.HISTORY + str(instrument) + '/minute?from=' +
                            date.strftime('%Y-%m-%d+%X') + '&to=' +
                            (date + timedelta(hours=24)).strftime('%Y-%m-%d+%X'), headers=self.get_headers())
        return resp.json()

    def get_daily_data(self, instrument, from_date, to_date):
        resp = requests.get(self.BASE_URL + self.HISTORY + instrument + '/day?from=' +
                            from_date.strftime('%Y-%m-%d+%X') + '&to=' + to_date.strftime('%Y-%m-%d+%X'),
                            headers=self.get_headers())
        return resp.json()

    def get_data(self, instrument, from_date, to_date, interval):
        url = '{}{}{}/{}?from={}&to={}'.format(self.BASE_URL, self.HISTORY, instrument, interval,
                                               from_date.strftime('%Y-%m-%d+%X'), to_date.strftime('%Y-%m-%d+%X'))
        resp = requests.get(url, headers=self.get_headers())
        return resp.json()

    def get_instrument_from_symbol(self, symbol):
        cur = self.conn.cursor()
        cur.execute('SELECT instrument FROM instrument where symbol=%s', [symbol])
        return int(cur.fetchone()[0])

    def get_headers(self):
        headers = {'Authorization': 'token {}:{}'.format(self.API_KEY, self.access_token)}
        return headers

    def push_instruments_to_database(self):
        conn = psycopg2.connect(host="localhost", database=self.DATABASE['NAME'], user=self.DATABASE['USERNAME'],
                                password=self.DATABASE['PASSWORD'])
        cur = conn.cursor()
        instruments = self.kite_connect.instruments(exchange='NSE')
        for instrument in instruments:
            self.create_table()
            cur.execute('INSERT INTO instrument (symbol, instrument, instrument_type, tick_size, name, exchange) '
                        'VALUES(\'{}\',{},\'{}\',{},\'{}\',\'{}\')'.format(instrument['tradingsymbol'],
                                                                           instrument['instrument_token'],
                                                                           instrument['instrument_type'],
                                                                           instrument['tick_size'],
                                                                           instrument['name'].replace('\'', ''),
                                                                           instrument['exchange']))
        conn.commit()

    def create_table(self):
        conn = psycopg2.connect(host="localhost", database=self.DATABASE['NAME'], user=self.DATABASE['USERNAME'],
                                password=self.DATABASE['PASSWORD'])
        cur = conn.cursor()
        cur.execute('DROP TABLE IF EXISTS instrument')
        conn.commit()
        cur.execute('CREATE TABLE instrument ('
                    'id SERIAL PRIMARY KEY NOT NULL,'
                    'symbol VARCHAR(60) NOT NULL,'
                    'instrument INTEGER NOT NULL,'
                    'instrument_type VARCHAR(60) NOT NULL,'
                    'tick_size DOUBLE PRECISION,'
                    'name VARCHAR(200) NOT NULL,'
                    'exchange VARCHAR(60) NOT NULL'
                    ')')
        conn.commit()


class Algorithm(object):
    NIFTY50 = ['ADANIPORTS', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL',
               'INFRATEL', 'CIPLA', 'COALINDIA', 'DRREDDY', 'EICHERMOT', 'GAIL', 'GRASIM', 'HCLTECH', 'HDFCBANK',
               'HEROMOTOCO', 'HINDALCO', 'HINDPETRO', 'HINDUNILVR', 'HDFC', 'ITC', 'ICICIBANK', 'IBULHSGFIN', 'IOC',
               'INDUSINDBK', 'INFY', 'KOTAKBANK', 'LT', 'LUPIN', 'M&M', 'MARUTI', 'NTPC', 'ONGC', 'POWERGRID',
               'RELIANCE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'UPL', 'ULTRACEMCO',
               'VEDL', 'WIPRO', 'YESBANK', 'ZEEL', ]

    def __init__(self, opening_increase=.1, opening_decrease=-.1, stop_loss=-.2):
        self.opening_increase = opening_increase
        self.opening_decrease = opening_decrease
        self.stop_loss = stop_loss

    def buy_symbol(self):
        pass

    def sell_symbol(self):
        pass

    def filter1(self, date_time=datetime.now(), exclude=None):
        zerodha = ZerodhaConnector()
        if exclude:
            [self.NIFTY50.remove(symbol) for symbol in exclude]

        positive_symbols = []
        negative_symbols = []
        for symbol in self.NIFTY50:
            positive_success = False
            negative_success = False
            instrument_id = zerodha.get_instrument_from_symbol(symbol=symbol)
            result = zerodha.get_data(instrument=instrument_id, from_date=date_time - timedelta(minutes=15),
                                      to_date=date_time, interval='minute')
            if result['status'] != 'success':
                raise Exception('API failed : {}'.format(result))
            initial_open = None
            for candle in result['data']['candles']:
                if not initial_open:
                    initial_open = candle[1]
                if ((candle[4] - initial_open) * 100 / initial_open) >= self.opening_increase:
                    positive_success = True
                    confidence = (abs((result['data']['candles'].pop())[4] - initial_open) / initial_open)
                    break
                if ((candle[4] - initial_open) * 100 / initial_open) <= self.opening_decrease:
                    negative_success = True
                    confidence = abs(((result['data']['candles'].pop())[4] - initial_open) / initial_open)
                    break
            if positive_success:
                positive_symbols.append({'symbol': symbol, 'confidence': (1 / confidence) if confidence != 0 else 0})
            if negative_success:
                negative_symbols.append({'symbol': symbol, 'confidence': (1 / confidence) if confidence != 0 else 0})
        return {'positive': positive_symbols, 'negative': negative_symbols}

    def start(self):
        pass


class AccountManager(object):
    amount = 50000

    def __init__(self, algorithm):
        self.algorithm = algorithm

    def get_current_amount_available(self):
        return self.amount

    def start(self, from_date_time=datetime.now()):
        symbols = None
        while not symbols:
            symbols = self.algorithm.filter1(from_date_time)
            from_date_time = from_date_time + timedelta(minutes=1)


# x = AccountManager(algorithm=Algorithm(opening_increase=.1, stop_loss=-.5))
# x.start(from_date_time=datetime(year=2017, month=6, day=25, hour=9, minute=15, second=0))

# x = Algorithm()
# y = x.filter1(date_time=datetime.now() - timedelta(days=2, hours=5))
# print(y)
# Response structure candle: [timestamp, open, high, low, close, volume]
# instrument_id = x.get_instrument_from_symbol(symbol='SBIN')
# y = x.get_intraday_data(instrument=instrument_id, date=datetime.date(year=2018, month=6, day=22))
# print(y)
# # x.push_instruments_to_database()


logger = logging.getLogger()
log_format = '[%(asctime)s] (levelname)s in %(module)s [%(pathname)s:%(lineno)d] - %(message)s'
formatter = logging.Formatter(log_format, '%m-%d %H:%M:%S')
handler = RotatingFileHandler('stocks.log', maxBytes=10000000, backupCount=10)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

logging.basicConfig(level=logging.DEBUG)

import glob
import json
import os
import time
from collections import OrderedDict
import datetime

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


# NIFTY50 = ['ADANIPORTS', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL',
#            'INFRATEL', 'CIPLA', 'COALINDIA', 'DRREDDY', 'EICHERMOT', 'GAIL', 'GRASIM', 'HCLTECH', 'HDFCBANK',
#            'HEROMOTOCO', 'HINDALCO', 'HINDPETRO', 'HINDUNILVR', 'HDFC', 'ITC', 'ICICIBANK', 'IBULHSGFIN', 'IOC',
#            'INDUSINDBK', 'INFY', 'KOTAKBANK', 'LT', 'LUPIN', 'M&M', 'MARUTI', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE',
#            'SBIN', 'SUNPHARMA', 'TCS', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'UPL', 'ULTRACEMCO', 'VEDL',
#            'WIPRO', 'YESBANK', 'ZEEL', ]
#
# # data_downloader = DataDownloader()
# # for symbol in NIFTY50:
# #     data_downloader.get_data_file(symbol=symbol, time_period='365 Days')
#
# DIRECTORY = os.path.dirname(os.path.abspath(__file__))
# DOWNLOADS = os.path.join(DIRECTORY, 'downloads')
# data_files = sorted(glob.glob(DOWNLOADS.replace('\\', '/') + '/' + '*.csv'))
#
# date_wise_change = OrderedDict()
# for file in data_files:
#     with open(file.replace('\\', '/')) as csv_reader:
#         dict_reader = csv.DictReader(csv_reader)
#         for line in dict_reader:
#             if line['Date'] not in date_wise_change.keys():
#                 date_wise_change[line['Date']] = OrderedDict()
#             date_wise_change[line['Date']][line['Symbol']] = (float(line['Open Price']) - float(
#                 line['Close Price'])) / float(line['Open Price'])
#
# whole_minimum = []
# for key, value in date_wise_change.iteritems():
#     sorted_data = sorted(value.items(), key=lambda x: x[1])
#     whole_minimum.append({key: sorted_data})
#     # minimum = {'Change': None, 'Symbol': None, 'Date': None}
#     # for symbol_name, change in value.iteritems():
#     #     if not minimum['Change'] or minimum['Change'] > change:
#     #         minimum['Change'] = change
#     #         minimum['Symbol'] = symbol_name
#     #         minimum['Date'] = key
#     # whole_minimum.append(minimum)
#
# print(json.dumps(whole_minimum))
#
#
# with open(os.path.join('data', 'equity_symbols.csv')) as csv_reader:
#     dict_reader = csv.DictReader(csv_reader)
#     data_downloader = DataDownloader()
#     for line in dict_reader:
#         data_downloader.get_data_file(symbol=line['SYMBOL'], time_period='365 Days')


class Algorithm(object):
    NIFTY50 = ['ADANIPORTS', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL',
               'INFRATEL', 'CIPLA', 'COALINDIA', 'DRREDDY', 'EICHERMOT', 'GAIL', 'GRASIM', 'HCLTECH', 'HDFCBANK',
               'HEROMOTOCO', 'HINDALCO', 'HINDPETRO', 'HINDUNILVR', 'HDFC', 'ITC', 'ICICIBANK', 'IBULHSGFIN', 'IOC',
               'INDUSINDBK', 'INFY', 'KOTAKBANK', 'LT', 'LUPIN', 'M&M', 'MARUTI', 'NTPC', 'ONGC', 'POWERGRID',
               'RELIANCE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'UPL', 'ULTRACEMCO',
               'VEDL', 'WIPRO', 'YESBANK', 'ZEEL', ]
    DIRECTORY = os.path.dirname(os.path.abspath(__file__))
    DOWNLOADS = os.path.join(DIRECTORY, 'downloads')
    data_files = sorted(glob.glob(DOWNLOADS.replace('\\', '/') + '/' + '*.csv'))
    api_key = 'R5F8JJNH1V4REZ4P'

    def __init__(self, count_symbols=5, success_percent=1, opening_duration=15, stop_loss=0.7):
        self.count_symbols = count_symbols
        self.success_percent = success_percent
        self.opening_duration = opening_duration
        self.stop_loss = stop_loss
        # calculate top 5 losers on previous day
        # For today, find symbols among top 5 losers which have increased by .5% within first 15 minutes
        # among these stocks, find number of stocks which have reached 1% hike during the day
        pass

    def get_daily_stock_file(self, symbol):
        pass

    def get_top_losers(self, date, total=5):
        # return top 5 loser symbols
        date_wise_change = OrderedDict()
        for date_file in self.data_files:
            with open(date_file.replace('\\', '/')) as csv_reader:
                dict_reader = csv.DictReader(csv_reader)
                for line in dict_reader:
                    if line['Date'] != date.strftime('%d-%b-%Y'):
                        continue
                    if line['Date'] not in date_wise_change.keys():
                        date_wise_change[line['Date']] = OrderedDict()
                    date_wise_change[line['Date']][line['Symbol']] = (float(line['Close Price']) - float(
                        line['Open Price'])) / float(line['Open Price'])
        whole_minimum = []
        for key, value in date_wise_change.iteritems():
            sorted_data = sorted(value.items(), key=lambda x: x[1])
            whole_minimum.append({key: sorted_data})
        return whole_minimum[0][date.strftime('%d-%b-%Y')][:5]

    def get_last_close_price(self, symbol, last_day_date):
        for date_file in self.data_files:
            with open(date_file.replace('\\', '/')) as csv_reader:
                lines = csv_reader.readlines()
                if lines[1][0] != symbol:
                    continue
            with open(date_file.replace('\\', '/')) as csv_reader:
                dict_reader = csv.DictReader(csv_reader)
                for line in dict_reader:
                    if line['Date'] != last_day_date.strftime('%d-%b-%Y'):
                        continue
                    return float(line['Close Price'])

    def filter_by_opening_increase(self, top_losers, date, target_percent=1, opening_duration=15,
                                   increase_required=0.5, stop_loss=-0.5):
        # return symbols who reached the target within first t minutes
        # Find file
        # Read the file and see the max price in first 15 minutes
        # If it has increased by more than target_percent, then count it in, otherwise filter it out
        passed_symbol = []
        for loser in top_losers:
            data_file = sorted(glob.glob(self.DOWNLOADS.replace('\\', '/') + '/minutes_data/' + date.strftime('%d')
                                         + date.strftime('%b%Y').upper() + '/' + loser + '.txt'))
            if not data_file:
                raise Exception('Minutes file not found.')
            date_wise_change = OrderedDict()
            max_price = None
            with open(data_file[0]) as text_reader:
                start_time = None
                for line in text_reader:
                    tups = line.split(',')
                    last_close = self.get_last_close_price(symbol=tups[0],
                                                           last_day_date=date - datetime.timedelta(days=-1))
                    row_time = datetime.time(hour=int(tups[2].split(':')[0]), minute=int(tups[2].split(':')[1]))
                    row_price = float(tups[4])
                    if not start_time:
                        start_time = row_time
                    if start_time + datetime.timedelta(minutes=opening_duration) < row_time:
                        break
                    if not max_price:
                        max_price = row_price
                    if max_price < row_price:
                        max_price = row_price
                    if (max_price - last_close) / last_close <= stop_loss:
                        print('We got miss.')
                    if (max_price - last_close) / last_close >= increase_required:
                        print('We got it.')
                    if line['Date'] not in date_wise_change.keys():
                        date_wise_change[line['Date']] = OrderedDict()
                    date_wise_change[line['Date']][line['Symbol']] = (float(line['Close Price']) - float(
                        line['Open Price'])) / float(line['Open Price'])
        whole_minimum = []
        for key, value in date_wise_change.iteritems():
            sorted_data = sorted(value.items(), key=lambda x: x[1])
            whole_minimum.append({key: sorted_data})
        return whole_minimum[0][date.strftime('%d-%b-%Y')][:5]

    def filter_by_success(self, right_symbols, date, stop_loss=0.7):
        # return symbols which have reached the target of 1% before reaching stop loss
        pass

    def calculate_success_rate(self, date):
        yesterday_loser_symbols = self.get_top_losers(date=date)
        level1_symbol = self.filter_by_opening_increase(top_losers=yesterday_loser_symbols)
        success_symbol = self.filter_by_success(right_symbols=level1_symbol)
        return (len(level1_symbol) - len(success_symbol)) * 100 / len(level1_symbol)


# algo = Algorithm()
# date_required = datetime.date(2017, 10, 3)
# success_rate = algo.get_top_losers(date=date_required)
# success_symbols = [tup[0] for tup in success_rate]
# level1_success = algo.filter_by_opening_increase(top_losers=success_symbols,
#                                                  date=date_required + datetime.timedelta(days=1), target_percent=1,
#                                                  opening_duration=15, increase_required=0.5, stop_loss=0.5)
# # success_rate = algo.calculate_success_rate(date=datetime.date(2017, 10, 1))
# print(success_rate)


from datetime import datetime

from clean_code import ThreadFactory


class StockTracker(object):
    """
    This class will track for a particular stock price goal and will call a success callback when successfully done,
    else call failure callback.
    Args:
        target: targetting price/volume
        type: type of the target: increase, decrease, change
        target_type_value: what's the change being targetted
        success: callback called when success, must take all kwargs
        failure: callback called when failure, must take all kwargs
    """
    TYPE_CHOICES = ['change']
    TARGET_CHOICES = ['price', 'volume']
    CHECK_INTERVAL = 30  # In seconds

    def __init__(self, target, type, target_type_value, start_from, end_at, success, failure):
        if type not in self.TYPE_CHOICES:
            raise Exception('Type choice for stock tracker not valid.')
        if target not in self.TARGET_CHOICES:
            raise Exception('Target not a valid choice.')
        self.target = target
        self.type = type
        self.success = success
        self.failure = failure
        self.target_type_value = target_type_value
        self.start_from = start_from
        self.end_at = end_at
        self.thread_factory = ThreadFactory(runner=self.start_tracking, interval=self.CHECK_INTERVAL)
        self.thread_factory.start()

    def start_tracking(self):
        if self.start_from <= datetime.now() <= self.end_at:
            if self.validate():
                self.success()
                self.thread_factory.stopper = True
            return True
        self.failure()
        self.thread_factory.stopper = True
        return True

    def validate(self):
        return False


from nsepy import get_history
from datetime import date

data = get_history(symbol="SBIN", start=date(2015, 1, 1), end=date(2015, 1, 31))
data[['Close']].plot()
# print(data)

from nsepy.history import get_price_list

prices = get_price_list(dt=date(2015, 1, 1))
print(prices)


class StockAlgorithm(object):
    def get_stock_data(self, symbol, start, end):
        data = get_history(symbol=symbol, start=start, end=end)


x = StockAlgorithm()
x.get_stock_data(symbol='SBIN', start=None, end=None)

from datetime import timedelta, datetime

from algorithms import Algorithm, Expectation
from zerodha import KiteHistory


class OpenDoors(Algorithm):
    def __init__(self, logger, opening_increase=.1, opening_decrease=.1, target_increase=1.0, target_decrease=1.0,
                 increase_stop_loss=.1, decrease_stop_loss=.1, time_slot=timedelta(minutes=15), date=None):
        self.logger = logger
        settings = {
            'opening_increase': opening_increase,
            'opening_decrease': opening_decrease,
            'target_increase': target_increase,
            'target_decrease': target_decrease,
            'increase_stop_loss': increase_stop_loss,
            'decrease_stop_loss': decrease_stop_loss,
            'time_slot': time_slot,
        }
        self.date = date
        self.increase_stop_loss = increase_stop_loss
        self.decrease_stop_loss = decrease_stop_loss
        if not date:
            self.date = datetime.now()
        self.stock_history = KiteHistory(exchange='NSE', logger=self.logger)
        self.transactions = []
        super(OpenDoors, self).__init__(settings=settings)

    def start_algorithm(self):
        self.logger.warning('Starting algorithm.')
        self.logger.info('date. {}'.format(self.date))
        stocks = self.stock_history.get_nifty50_sorted_by_change(date=self.date)
        gainers = stocks[-1:]
        gainers.reverse()
        losers = stocks[:1]
        for stock in (gainers + losers):
            trans = Expectation(logger=self.logger, type='buy', stock=stock[0], trigger_change=.1, amount=10000,
                                target_change=.5, stop_loss_percent=self.increase_stop_loss, date_time=self.date)
            self.transactions.append(trans)
            trans = Expectation(logger=self.logger, type='sell', stock=stock[0], trigger_change=.1, amount=10000.0,
                                target_change=.5, stop_loss_percent=self.decrease_stop_loss, date_time=self.date)
            self.transactions.append(trans)
            self.logger.info('Created {} transactions.'.format(len(self.transactions)))
        self.stop_algorithm()

    def stop_algorithm(self):
        self.logger.info('Stop Algorithm.')
        stoppers = [False]
        previous_stopper = stoppers
        while not all(stoppers):
            stoppers = []
            for index in range(len(self.transactions)):
                stoppers.append(self.transactions[index].thread_factory.stopper)
            time.sleep(10)
            if stoppers != previous_stopper:
                self.logger.info('Stopper: {}'.format(stoppers))
                previous_stopper = stoppers
        self.total_profit = 0
        for trans in self.transactions:
            self.total_profit += trans.price_result
        self.logger.info('Final profit: {}'.format(self.total_profit))
