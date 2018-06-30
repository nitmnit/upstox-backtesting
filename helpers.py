import json
import logging
import time
import urlparse
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import psycopg2
import requests
from kiteconnect import KiteConnect, KiteTicker
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

import settings


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

class DbCon(object):

    def __init__(self):
        self.con = psycopg2.connect(host=settings.DATABASE['HOST'], database=settings.DATABASE['NAME'],
                                    user=settings.DATABASE['USERNAME'],
                                    password=settings.DATABASE['PASSWORD'])

    def create_transactions_table(self):
        cur = self.con.cursor()
        cur.execute('DROP TABLE IF EXISTS transactions')
        self.con.commit()
        cur.execute('CREATE TABLE transactions ('
                    'id SERIAL PRIMARY KEY NOT NULL,'
                    'symbol VARCHAR(60) NOT NULL,'
                    'instrument INTEGER NOT NULL,'
                    'instrument_type VARCHAR(60) NOT NULL,'
                    'tick_size DOUBLE PRECISION,'
                    'name VARCHAR(200) NOT NULL,'
                    'exchange VARCHAR(60) NOT NULL'
                    ')')
        self.con.commit()

    def create_tokens_table(self):
        cur = self.con.cursor()
        cur.execute('DROP TABLE IF EXISTS tokens')
        self.con.commit()
        cur.execute('CREATE TABLE tokens ('
                    'id SERIAL PRIMARY KEY NOT NULL,'
                    'access_token VARCHAR(500) NOT NULL'
                    ')')
        self.con.commit()

    def get_token_if_exists(self):
        cur = self.con.cursor()
        cur.execute('SELECT access_token FROM tokens LIMIT 1')
        result = cur.fetchone()
        if result:
            return result[0]
        return None

    def set_token(self, token):
        cur = self.con.cursor()
        cur.execute('DELETE FROM tokens;')
        cur.execute('INSERT INTO tokens (access_token) VALUES (%s);', [token])
        self.con.commit()


def get_date():
    if settings.DEBUG:
        if datetime.today().strftime("%a") not in ['Sat', 'Sun']:
            return datetime.today().date()
        else:
            return (datetime.today() - timedelta(days=2)).date()
