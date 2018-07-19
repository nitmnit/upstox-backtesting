import hashlib
import json
import time
import urlparse
from datetime import timedelta, datetime, date as ddate

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


# https://kite.trade/forum/discussion/1994/a-curated-list-of-things-related-to-kite-connect-api
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

    def __init__(self, exchange='NSE', logger=None):
        self.logger = logger
        self.exchange = exchange
        self.con = KiteConnect(api_key=settings.KITE['API_KEY'])
        access_token = self.get_access_token()
        self.con.set_access_token(access_token)

    def log(self, message, level='INFO'):
        if self.logger:
            self.logger.info(message)

    def get_access_token(self):
        db_con = DbCon()
        access_token = db_con.get_token_if_exists()
        if access_token and self.test_access_token(token=access_token):
            return access_token
        access_token = self.create_new_access_token()
        db_con.set_token(token=access_token)
        return access_token

    def create_new_access_token(self):
        self.log('Creating new access token.')
        request_token = self.get_request_token()
        data = self.con.generate_session(request_token, api_secret=settings.KITE['API_SECRET'])
        if 'access_token' in data:
            self.log('Created new Access token. {}'.format(data['access_token']))
            return data['access_token']
        else:
            raise Exception('Token not found.')

    def test_access_token(self, token):
        try:
            self.con.set_access_token(access_token=token)
            self.con.holdings()
            return True
        except (TokenException, ConnectionError):
            self.log('Access token validation failed. {}'.format(token))
            return False

    @wait_response
    def get_quote(self, instrument_id):
        quote = self.con.quote(instrument_id)
        self.log('Getting quote. {}'.format(quote))
        return quote

    @wait_response
    def get_quotes(self, instruments):
        assert (type(instruments) == list)
        quotes = self.con.quote(instruments)
        self.log('Getting Group quotes. {}'.format(quotes))
        return quotes

    @wait_response
    def place_bracket_order_at_market_price(self, symbol, transaction_type, quantity, square_off, stop_loss, price):
        if transaction_type == 'buy':
            transaction_type = self.con.TRANSACTION_TYPE_BUY
        else:
            transaction_type = self.con.TRANSACTION_TYPE_SELL
        order_id = self.con.place_order(variety=self.con.VARIETY_BO,
                                        exchange=self.con.EXCHANGE_NSE,
                                        tradingsymbol=symbol,
                                        transaction_type=transaction_type,
                                        quantity=quantity,
                                        product=self.con.PRODUCT_BO,
                                        order_type=self.con.ORDER_TYPE_LIMIT,
                                        disclosed_quantity=quantity / 10 + 1,
                                        squareoff=square_off,
                                        stoploss=stop_loss,
                                        price=price,
                                        validity=self.con.VALIDITY_DAY)
        self.log('Order Place: {}'.format(order_id))
        return order_id

    def get_daily_open_price(self, instrument, date):
        start_date = datetime(year=date.year, month=date.month, day=date.day, hour=9, minute=15, second=0)
        end_date = datetime(year=date.year, month=date.month, day=date.day, hour=15, minute=30, second=0)
        data = self.get_minutes_candles(instrument=instrument, from_date=start_date, to_date=end_date)
        return data[0]['open']

    def get_nifty50_open_price(self):
        nifty_instruments = [instrument for symbol, instrument in settings.NIFTY50.iteritems()]
        data = self.get_quotes(instruments=nifty_instruments)
        open_prices = {}
        for instrument, quote in data.iteritems():
            if 'ohlc' in quote and 'open' in quote['ohlc'] and quote['ohlc']['open'] != 0:
                open_prices[str(instrument)] = quote[str(instrument)]['ohlc']['open']
        return open_prices

    def get_daily_close_price(self, instrument, date):
        start_date = datetime(year=date.year, month=date.month, day=date.day, hour=9, minute=15, second=0)
        end_date = datetime(year=date.year, month=date.month, day=date.day, hour=15, minute=30, second=0)
        data = self.get_minutes_candles(instrument=instrument, from_date=start_date, to_date=end_date)
        return data[-1]['close']

    @staticmethod
    def get_key(*args):
        hash_object = hashlib.md5(';'.join([str(x) for x in args]))
        return hash_object.hexdigest()

    @wait_response
    def get_minutes_candles(self, instrument, from_date, to_date):
        if to_date > datetime.now():
            to_date = datetime.now()
        if settings.REDIS['IS_ENABLED']:
            data = r.hget('get_minutes_candles', self.get_key(instrument, from_date, to_date))
            if not data or len(data) < 3:
                data = self.con.historical_data(instrument_token=instrument, from_date=from_date, to_date=to_date,
                                                interval='minute')
                for dl in data:
                    dl['date'] = dl['date'].strftime('%m/%d/%Y %I:%M:%S %p')
                r.hset('get_minutes_candles', self.get_key(instrument, from_date, to_date), json.dumps(data))
            else:
                data = json.loads(data)
            for dl in data:
                dl['date'] = datetime.strptime(dl['date'], '%m/%d/%Y %I:%M:%S %p')
        return data

    def get_top_gainers(self, date, number=5):
        data = self.get_nifty50_sorted_by_change(date=date)
        if len(data) >= number:
            return data[-number:].reverse()
        return data

    def get_nifty50_sorted_by_change(self, date):
        stocks_change_list = []
        for symbol, instrument in settings.NIFTY50.items():
            open_price = self.get_daily_open_price(instrument=instrument, date=date)
            close_price = self.get_daily_close_price(instrument=instrument, date=date)
            stocks_change_list.append((self.get_stock(instrument=instrument), symbol,
                                       100.0 * (close_price - open_price) / open_price), )
        data = sorted(stocks_change_list, key=lambda x: x[2])
        return data

    def get_top_losers(self, date, number=5):
        data = self.get_nifty50_sorted_by_change(date=date)
        if len(data) >= number:
            self.log('Top losers :  data- {}\n data: {}'.format(date, data[:number]))
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
        self.log('Getting request token.')
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
        self.log('Got request token. {}'.format(request_token))
        return request_token

    def get_nifty50_today_minutes_data_files(self):
        for symbol, instrument in settings.NIFTY50.items():
            with open('data/report_today_' + str(symbol) + '.csv', 'w') as fi:
                data_c = self.get_minutes_candles(from_date=datetime.now().date(),
                                                  to_date=datetime.now() + timedelta(days=1), instrument=instrument)
                fi.write(','.join([str(key) for key, x in data_c[0].items()]))
                for dt in data_c:
                    fi.write(','.join([str(x) for key, x in dt.items()]) + '\n')
