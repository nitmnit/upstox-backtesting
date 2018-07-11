import hashlib
import json
import time
import urlparse
from datetime import timedelta

import psycopg2
from kiteconnect import KiteConnect
from kiteconnect.exceptions import TokenException
import redis
from requests.exceptions import ConnectionError

import settings
from db_connector import DbCon
from helpers import wait_response
from stocks import Candle, Stock
from webpage_interaction import SeleniumConnector

r = redis.StrictRedis(host='localhost', port=6379)


class KiteCon(object):
    def __init__(self, exchange, logger):
        self.logger = logger
        self.exchange = exchange

    def buy(self, instrument, price, quantity, order_type, stop_loss=None):
        self.logger.info('Bought the stock buy.')
        return 'price'

    def buy_at_market_price(self, instrument_id, amount, order_type, stop_loss=None):
        self.logger.info('Bought the stock.')
        return 'price'

    def sell(self, instrument_id, price, quantity, order_type, stop_loss=None):
        return 'price'

    def sell_at_market_price(self, instrument_id, amount, order_type, stop_loss=None):
        self.logger.info('Sold the stock.')
        return 'price'

    def orders(self):
        pass

    @property
    def equity(self):
        pass

    @property
    def commodity(self):
        pass

    def holdings(self):
        pass

    def positions(self):
        pass


class KiteHistory(object):

    def __init__(self, exchange, logger):
        self.logger = logger
        self.exchange = exchange
        self.con = KiteConnect(api_key=settings.KITE['API_KEY'])
        access_token = self.get_access_token()
        self.con.set_access_token(access_token)

    def get_access_token(self):
        db_con = DbCon()
        access_token = db_con.get_token_if_exists()
        if access_token and self.test_access_token(token=access_token):
            return access_token
        access_token = self.create_new_access_token()
        db_con.set_token(token=access_token)
        return access_token

    def create_new_access_token(self):
        self.logger.info('Creating new access token.')
        request_token = self.get_request_token()
        data = self.con.generate_session(request_token, api_secret=settings.KITE['API_SECRET'])
        if 'access_token' in data:
            self.logger.info('Created new Access token. {}'.format(data['access_token']))
            return data['access_token']
        else:
            raise Exception('Token not found.')

    def test_access_token(self, token):
        try:
            self.con.set_access_token(access_token=token)
            self.con.holdings()
            return True
        except (TokenException, ConnectionError):
            self.logger.info('Access token validation failed. {}'.format(token))
            return False

    @wait_response
    def get_quote(self, instrument_id):
        quote = self.con.quote(instrument_id)
        self.logger.info('Getting quote. {}'.format(quote))
        return quote

    @wait_response
    def get_open_price(self, instrument, date):
        if settings.REDIS['IS_ENABLED']:
            data = r.hget('get_open_price', self.get_key(instrument, date))
            if not data:
                data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                                to_date=date + timedelta(days=1),
                                                interval='day')
                for dl in data:
                    del dl['date']
                r.hset('get_open_price', self.get_key(instrument, date), json.dumps(data))
            else:
                data = json.loads(data)
        return data[0]['open']

    @wait_response
    def get_close_price(self, instrument, date):
        if settings.REDIS['IS_ENABLED']:
            data = r.hget('get_close_price', self.get_key(instrument, date))
            if not data:
                data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                                to_date=date + timedelta(days=1),
                                                interval='day')
                for dl in data:
                    del dl['date']
                r.hset('get_close_price', self.get_key(instrument, date), json.dumps(data))
            else:
                data = json.loads(data)
        return data[0]['close']

    def get_key(self, *args):
        hash_object = hashlib.md5(';'.join([str(x) for x in args]))
        return hash_object.hexdigest()

    @wait_response
    def get_minutes_candles(self, instrument, from_date, to_date):
        if settings.REDIS['IS_ENABLED']:
            data = r.hget('get_minutes_candles', self.get_key(instrument, from_date, to_date))
            if not data:
                data = self.con.historical_data(instrument_token=instrument, from_date=from_date, to_date=to_date,
                                                interval='minute')
                for dl in data:
                    del dl['date']
                r.hset('get_minutes_candles', self.get_key(instrument, from_date, to_date), json.dumps(data))
            else:
                data = json.loads(data)
        return data

    @wait_response
    def get_top_gainers(self, date, number=5):
        if settings.REDIS['IS_ENABLED']:
            data = r.hget('get_top_gainers', self.get_key(date, number))
            if not data:
                data = self.get_nifty50_sorted_by_change(date=date)
                r.hset('get_top_gainers', self.get_key(date, number), json.dumps(data))
            else:
                data = json.loads(data)
        if len(data) >= number:
            return data[-number:].reverse()
        return data

    @wait_response
    def get_nifty50_sorted_by_change(self, date):
        if date.strftime('%a') in ['Sat', 'Sun']:
            raise Exception("Invalid date input.")
        total_data = []
        for symbol, instrument in settings.NIFTY50.items():
            data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                            to_date=date + timedelta(days=1),
                                            interval='day')
            candle = Candle(data=data[0])
            total_data.append((self.get_stock(instrument=instrument), symbol,
                               100.0 * (candle.close - candle.open) / candle.open), )
        data = sorted(total_data, key=lambda x: x[2])
        return data

    @wait_response
    def get_top_losers(self, date, number=5):
        if settings.REDIS['IS_ENABLED']:
            data = r.hget('get_top_losers', self.get_key(date, number))
            if not data:
                data = self.get_nifty50_sorted_by_change(date=date)
                r.hset('get_top_losers', self.get_key(date, number), json.dumps(data))
            else:
                data = json.loads(data)
        if len(data) >= number:
            self.logger.info('Top losers :  data- {}\n data: {}'.format(date, data[:number]))
            return data[:number]

    @wait_response
    def get_nifty50_stocks(self):
        stocks = []
        for symbol, instrument in settings.NIFTY50.items():
            stock = self.get_stock(instrument=instrument)
            stocks.append(stock)
        return stocks

    @wait_response
    def get_stock(self, instrument):
        conn = psycopg2.connect(host=settings.DATABASE['HOST'], database=settings.DATABASE['NAME'],
                                user=settings.DATABASE['USERNAME'], password=settings.DATABASE['PASSWORD'])
        cur = conn.cursor()
        cur.execute("SELECT * FROM instrument WHERE instrument = {};".format(instrument))
        data = cur.fetchone()
        stock = Stock(id=data[0], name=data[5], symbol=data[1], instrument=data[2], instrument_type=data[3],
                      tick_size=data[4], exchange=data[6])
        return stock

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
        self.logger.info('Getting request token.')
        con = SeleniumConnector(logger=self.logger)
        con.driver.get(self.con.login_url())
        time.sleep(3)
        username_input = con.driver.find_element_by_css_selector('input[type="text"]')
        password_input = con.driver.find_element_by_css_selector('input[type="password"]')
        submit_button = con.driver.find_element_by_css_selector('button[type="submit"]')
        username_input.send_keys(settings.KITE['USERNAME'])
        password_input.send_keys(settings.KITE['PASSWORD'])
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
        self.logger.info('Got request token. {}'.format(request_token))
        return request_token
