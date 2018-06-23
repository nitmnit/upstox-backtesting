import json
import logging
import time
import urlparse
import datetime
from logging.handlers import RotatingFileHandler

import psycopg2
import requests
from kiteconnect import KiteConnect, KiteTicker
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options


class SeleniumConnector(object):
    def __init__(self, is_headless=True, ):
        chrome_options = Options()
        if is_headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('window-size=1920,1080')
        # chrome_options.add_argument("download.default_directory=C:/Users/Administrator/PycharmProjects/Stock/downloads")
        prefs = {'download.default_directory': 'C:/Users/Administrator/PycharmProjects/Stock/downloads'}
        chrome_options.add_experimental_option('prefs', prefs)
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['loggingPrefs'] = {"browser": "SEVERE"}
        self.driver = webdriver.Chrome(executable_path='/home/nitin/Desktop/stocks/chromedriver',
                                       desired_capabilities=DesiredCapabilities.CHROME, chrome_options=chrome_options)
        self.wait_time = 3


logger = logging.getLogger()
log_format = '[%(asctime)s] (levelname)s in %(module)s [%(pathname)s:%(lineno)d] - %(message)s'
formatter = logging.Formatter(log_format, '%m-%d %H:%M:%S')
handler = RotatingFileHandler('stocks.log', maxBytes=10000000, backupCount=10)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

logging.basicConfig(level=logging.DEBUG)


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
                            (date + datetime.timedelta(hours=24)).strftime('%Y-%m-%d+%X'), headers=self.get_headers())
        return resp.json()

    def get_daily_data(self, instrument, from_date, to_date):
        resp = requests.get(self.BASE_URL + self.HISTORY + instrument + '/minute?from=' +
                            from_date.strftime('%Y-%m-%d+%X') + '&to=' + to_date.strftime('%Y-%m-%d+%X'),
                            headers=self.get_headers())
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
        self.create_table()
        for instrument in instruments:
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


x = ZerodhaConnector()
instrument_id = x.get_instrument_from_symbol(symbol='SBIN')
y = x.get_intraday_data(instrument=instrument_id, date=datetime.date(year=2018, month=6, day=22))
print(y)
# x.push_instruments_to_database()
