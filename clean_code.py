import math
from abc import abstractmethod
from threading import Thread
import time
import urlparse
from datetime import datetime, timedelta, datetime as ddatetime, time as ttime

import psycopg2
from kiteconnect import KiteConnect, KiteTicker
from kiteconnect.exceptions import TokenException
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

import settings
from helpers import DbCon, get_date

import logging.config

logger = logging.getLogger(__name__)

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,  # this fixes the problem
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s [%(pathname)s:%(lineno)d] - %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'freaky_bananas.log',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 100,
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
})

total_amount = 100000


class SeleniumConnector(object):
    def __init__(self, is_headless=False, ):
        logger.info('Selenium Connect Started')
        chrome_options = Options()
        if is_headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('window-size=1920,1080')
        # chrome_options.add_argument("download.default_directory=C:/Users/Administrator/PycharmProjects/Stock/downloads")
        # prefs = {'download.default_directory': 'C:/Users/Administrator/PycharmProjects/Stock/downloads'}
        # chrome_options.add_experimental_option('prefs', prefs)
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['loggingPrefs'] = {"browser": "SEVERE"}
        self.driver = webdriver.Chrome(executable_path='./chromedriver',
                                       desired_capabilities=DesiredCapabilities.CHROME, chrome_options=chrome_options)
        self.wait_time = 3
        logger.info('Selenium Connect Ended')


class ThreadFactory(object):
    def __init__(self, runner, interval=1):
        self.interval = interval
        self.thread = Thread(target=self.run, args=())
        self.stopper = True
        self.suspend = False
        self.runner = runner
        self.thread.daemon = True
        self.name = runner.__name__

    def run(self):
        while not self.stopper:
            if self.suspend:
                time.sleep(self.interval)
                continue
            if not self.runner():
                self.stopper = True
            time.sleep(self.interval)

    def start(self):
        self.stopper = False
        self.thread.start()


class Stock(object):
    def __init__(self, id, name, symbol, instrument, instrument_type, tick_size, exchange):
        self.id = id
        self.name = name
        self.symbol = symbol
        self.instrument = instrument
        self.instrument_type = instrument_type
        self.tick_size = tick_size
        self.exchange = exchange

    def __repr__(self):
        return '{}-{}-{}'.format(self.symbol, self.instrument, self.exchange)


class KiteCon(object):
    def __init__(self, exchanges):
        logger.info('KiteCon started.')
        self.exchanges = exchanges

    def buy(self, instrument_id, price, quantity, order_type, stop_loss=None):
        return 'price'

    def buy_at_market_price(self, instrument_id, amount, order_type, stop_loss=None):
        logger.info('Bought the stock.')
        return 'price'

    def sell(self, instrument_id, price, quantity, order_type, stop_loss=None):
        return 'price'

    def sell_at_market_price(self, instrument_id, amount, order_type, stop_loss=None):
        logger.info('Sold the stock.')
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


class Candle(object):
    def __init__(self, data):
        self.volume = data['volume']
        self.high = data['high']
        self.low = data['low']
        self.date = data['date']
        self.close = data['close']
        self.open = data['open']


class KiteHistory(object):

    def __init__(self, exchanges):
        self.exchanges = exchanges
        self.con = KiteConnect(api_key=settings.KITE['API_KEY'])
        access_token = self.get_access_token()
        self.con.set_access_token(access_token)

    def get_access_token(self):
        db_con = DbCon()
        access_token = db_con.get_token_if_exists()
        logger.info('Got access token from database. {}'.format(access_token))
        if access_token and self.test_access_token(token=access_token):
            return access_token
        access_token = self.create_new_access_token()
        db_con.set_token(token=access_token)
        return access_token

    def create_new_access_token(self):
        logger.info('Creating new access token.')
        request_token = self.get_request_token()
        data = self.con.generate_session(request_token, api_secret=settings.KITE['API_SECRET'])
        if 'access_token' in data:
            logger.info('Created new Access token. {}'.format(data['access_token']))
            return data['access_token']
        else:
            raise Exception('Token not found.')

    def test_access_token(self, token):
        try:
            self.con.set_access_token(access_token=token)
            out = self.con.holdings()
            logger.info('Access token validation succeeded. {}'.format(token))
            return True
        except TokenException:
            logger.info('Access token validation failed. {}'.format(token))
            return False

    def get_quote(self, instrument_id):
        quote = self.con.quote(instrument_id)
        logger.info('Getting quote. {}'.format(quote))
        return quote

    def get_open_price(self, instrument, date):
        data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                        to_date=date + timedelta(days=1),
                                        interval='day')
        logger.info('Get open price. {}'.format(data[0]['open']))
        return data[0]['open']

    def get_minutes_candles(self, instrument_id, from_date, to_date):
        daily = self.con.historical_data(instrument_token=instrument_id, from_date=from_date, to_date=to_date,
                                         interval='minute')
        return daily

    def get_top_gainers(self, date, number=5):
        data = self.get_nifty50_sorted_by_change(date=date)
        logger.info('Got top gainers candle. date - {}\n data: {}'.format(date, data))
        if len(data) >= number:
            return data[-number:].reverse()

    def get_nifty50_sorted_by_change(self, date):
        if date.strftime('%a') in ['Sat', 'Sun']:
            raise Exception("Invalid date input.")
        logger.info('Get nifty50 changes Nifty 50 data: date {}'.format(date))
        total_data = []
        for symbol, instrument in settings.NIFTY50.items():
            data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                            to_date=date + timedelta(days=1),
                                            interval='day')
            candle = Candle(data=data[0])
            total_data.append((self.get_stock(instrument=instrument), symbol,
                               100.0 * (candle.close - candle.open) / candle.open), )
        data = sorted(total_data, key=lambda x: x[2])
        logger.info('Nifty 50 sorted changes :  data- {}\n data: {}'.format(date, data))
        return data

    def get_top_losers(self, date, number=5):
        data = self.get_nifty50_sorted_by_change(date=date)
        if len(data) >= number:
            logger.info('Top losers :  data- {}\n data: {}'.format(date, data[:number]))
            return data[:number]

    def get_nifty50_stocks(self):
        stocks = []
        for symbol, instrument in settings.NIFTY50.items():
            stock = self.get_stock(instrument=instrument)
            stocks.append(stock)
        logger.info('Top nifty 50 stocks: data: {}'.format(stocks))
        return stocks

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
        logger.info('Getting request token.')
        con = SeleniumConnector()
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
        logger.info('Got request token. {}'.format(request_token))
        return request_token


class Transaction(object):
    """
    This class holds one transaction to be made for profit, suggested by the algorithm
    Args
        type: buy/sell
        stock: Stock instance
        thread_interval: interval for thread in seconds
    """
    thread_interval = .3
    change_range = 0.1

    def __init__(self, type, stock, trigger_change, amount, target_change, stop_loss_percent, date_time=None):
        logger.info('Starting transaction \ntype: {} \nstock: {} \ntrigger_change: {} \namout: {} \ntarget_change: {} '
                    '\n stop_loss_percent: {} \n'.format(type, stock, trigger_change, amount, target_change,
                                                         stop_loss_percent))
        self.type = type
        self.stock = stock
        self.trigger_change = trigger_change
        self.target_change = target_change
        self.stop_loss_percent = stop_loss_percent
        self.stock_history = KiteHistory(exchanges='NSE')
        self.stock_app = KiteCon(exchanges='NSE')
        self.transaction_price = None  # Price at square off
        self.transaction_close_price = None  # Price at the end of the day
        self.trigger_success = None
        self.trigger_price = None  # Price at trigger
        self.close_success = None
        self.amount = amount
        self.price_result = None
        self.date_time = date_time
        self.open_price = self.stock_history.get_open_price(instrument=self.stock.instrument, date=date_time.date())
        self.time_counter = 0
        self.thread_factory = ThreadFactory(runner=self.wait_for_trigger, interval=self.thread_interval)
        self.thread_factory.start()

    def wait_for_trigger(self):
        assert bool(self.trigger_change)
        if settings.DEBUG:
            time_simulated = self.date_time + timedelta(seconds=self.time_counter)
            if not self.validate_date_time(time_simulated):
                logger.info('Failed to trigger the price.')
                self.close_transaction()
                return
            quote = self.stock_history.get_minutes_candles(self.stock.instrument, from_date=time_simulated,
                                                           to_date=time_simulated + timedelta(seconds=60 * 2))
            self.time_counter += 60 * 1
            price = quote[0]['close']
        else:
            quote = self.stock_history.get_quote(self.stock.instrument)
            price = quote.price
        if self.type == 'buy':
            target_range = (self.open_price * (1 + self.trigger_change / 100),
                            self.open_price * (1 + (self.trigger_change + self.change_range) / 100))
            print('buy trigger')
            print(target_range)
            print(price)
            if target_range[0] <= price <= target_range[1]:
                logger.warning('Buy trigger successful. Stock: {} '
                               '\nOpen Price: {} \nBought at: {}'.format(self.stock, self.open_price, price))
                self.trigger_success = True
        elif self.type == 'sell':
            target_range = (self.open_price * (1 - (self.trigger_change + self.change_range) / 100),
                            self.open_price * (1 - self.trigger_change / 100))
            if target_range[0] <= price <= target_range[1]:
                logger.warning('Sell trigger successful. Stock: {} '
                               '\nOpen Price: {} \nSold at: {}'.format(self.stock, self.open_price, price))
                self.trigger_success = True
            print('sell trigger')
            print(target_range)
            print(price)
        if self.trigger_success is not None and self.trigger_success:
            self.trigger_price = price
            if self.type == 'buy':
                self.trigger_price = self.stock_app.buy_at_market_price(instrument_id=self.stock.instrument,
                                                                        amount=self.amount, order_type='market',
                                                                        stop_loss=None)
            elif self.type == 'sell':
                self.trigger_price = self.stock_app.sell_at_market_price(instrument_id=self.stock.instrument,
                                                                         amount=self.amount, order_type='market',
                                                                         stop_loss=None)
            else:
                raise NotImplemented
            self.trigger_price = price  # Remove this in production
            self.thread_factory.runner = self.wait_for_square_off
            self.time_counter = 0
        return True

    def validate_date_time(self, date_time):
        if ttime(hour=9, minute=15, second=0) <= date_time.time() <= ttime(hour=15, minute=29, second=0):
            return True
        return False

    def wait_for_square_off(self):
        assert bool(self.trigger_price)
        if settings.DEBUG:
            time_simulated = self.date_time + timedelta(seconds=self.time_counter)
            if not self.validate_date_time(time_simulated):
                logger.info('Failed to square off the price.')
                self.close_transaction()
            quote = self.stock_history.get_minutes_candles(self.stock.instrument, from_date=time_simulated,
                                                           to_date=time_simulated + timedelta(seconds=60 * 2))
            self.time_counter += 60 * 1
        else:
            quote = self.stock_history.get_quote(self.stock.instrument)
        if settings.DEBUG:
            price = quote[0]['close']
        else:
            price = quote.price
        if self.type == 'buy':
            target_range = (self.open_price * (1 - (self.trigger_change + self.change_range) / 100),
                            self.open_price * (1 - self.trigger_change / 100))
            if target_range[0] <= price <= target_range[1]:
                self.close_success = True
                logger.warning('Sell square off successful. Stock: {} '
                               '\nOpen Price: {} \nSold at: {}'.format(self.stock, self.open_price, price))
            elif price < (self.trigger_price * (1 - self.stop_loss_percent / 100)):
                self.close_success = False
                logger.warning('Sell square off failed. Stock: {} '
                               '\nOpen Price: {} \nSold at: {}'.format(self.stock, self.open_price, price))
        elif self.type == 'sell':
            target_range = (self.open_price * (1 + self.trigger_change / 100),
                            self.open_price * (1 + (self.trigger_change + self.change_range) / 100))
            if target_range[0] <= price <= target_range[1]:
                self.close_success = True
                logger.warning('Buy square off successful. Stock: {} '
                               '\nOpen Price: {} \nBought at: {}'.format(self.stock, self.open_price, price))
            elif price > (self.trigger_price * (1 + self.stop_loss_percent / 100)):
                self.close_success = False
                logger.warning('Buy square off failed. Stock: {} '
                               '\nOpen Price: {} \nBought at: {}'.format(self.stock, self.open_price, price))
        if self.close_success is not None:
            if self.type == 'buy':
                self.transaction_price = self.stock_app.sell_at_market_price(instrument_id=self.stock.instrument,
                                                                             amount=self.amount, order_type='market',
                                                                             stop_loss=None)
            elif self.type == 'sell':
                self.transaction_price = self.stock_app.buy_at_market_price(instrument_id=self.stock.instrument,
                                                                            amount=self.amount, order_type='market',
                                                                            stop_loss=None)
            else:
                raise NotImplemented
            self.transaction_price = price
            self.transaction_close_price = price
            self.close_transaction()
            return False
        return True

    def close_transaction(self):
        logger.error('Closing transaction. {}'.format(self.stock))
        if self.trigger_success:
            quantity = math.floor(self.amount / self.trigger_price)
            price_percentage = (self.trigger_price - self.transaction_close_price) * quantity * 14.0
            if self.close_success:
                self.price_result = abs(price_percentage)
            else:
                self.price_result = -abs(price_percentage)
        else:
            self.price_result = 0
        self.thread_factory.stopper = True


class Algorithm(object):
    def __init__(self, settings):
        self.settings = settings

    @abstractmethod
    def start_algorithm(self): pass

    def create_transaction(self, type, stock, target_price, stop_loss_percent): pass

    def end_algorithm(self): pass


class OpenDoors(Algorithm):
    def __init__(self, opening_increase=.1, opening_decrease=.1, target_increase=.5, target_decrease=.5,
                 increase_stop_loss=.3, decrease_stop_loss=.3, time_slot=timedelta(minutes=15), date=None):
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
        if not date:
            self.date = datetime.now()
        self.stock_history = KiteHistory(exchanges='NSE')
        self.transactions = []
        super(OpenDoors, self).__init__(settings=settings)

    def start_algorithm(self):
        logger.warning('Starting algorithm. {}')
        logger.info('date. {}'.format(self.date))
        stocks = self.stock_history.get_nifty50_sorted_by_change(date=self.date)
        gainers = stocks[-1:]
        gainers.reverse()
        losers = []
        # losers = stocks[:5]
        for stock in (gainers + losers):
            trans = Transaction(type='buy', stock=stock[0], trigger_change=.1, amount=10000, target_change=.5,
                                stop_loss_percent=100,
                                date_time=self.date)
            self.transactions.append(trans)
            trans = Transaction(type='sell', stock=stock[0], trigger_change=.1, amount=10000.0, target_change=.5,
                                stop_loss_percent=100,
                                date_time=self.date)
            self.transactions.append(trans)
        logger.warning('Created {} transactions.'.format(len(self.transactions)))
        self.stop_algorithm()

    def stop_algorithm(self):
        logger.info('Into Stop Algorithm.')
        stoppers = [False]
        previous_stopper = stoppers
        while not all(stoppers):
            if stoppers != previous_stopper:
                logger.info('Stopper: {}'.format(stoppers))
                previous_stopper = stoppers
            stoppers = []
            for index in range(len(self.transactions)):
                stoppers.append(self.transactions[index].thread_factory.stopper)
            time.sleep(10)
        self.total_profit = 0
        for trans in self.transactions:
            self.total_profit += trans.price_result
        logger.info('Final profit: {}'.format(self.total_profit))


start_date = ddatetime(year=2018, month=6, day=27, hour=9, minute=18, second=0)
end_date = ddatetime(year=2018, month=6, day=27, hour=9, minute=18, second=0)
current_date = start_date
master_profit = 0
while start_date <= current_date <= end_date:
    x = OpenDoors(date=current_date)
    x.start_algorithm()
    master_profit += x.total_profit
    current_date = current_date + timedelta(days=1)

logger.info('Master Profit: {}'.format(master_profit))
