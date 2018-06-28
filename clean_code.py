from abc import abstractmethod
from threading import Thread
import time
import urlparse
from datetime import datetime, timedelta

import psycopg2
from kiteconnect import KiteConnect, KiteTicker
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

import settings

total_amount = 100000


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


class KiteCConnect(object):
    def __init__(self, exchanges):
        self.exchanges = exchanges

    def buy(self, instrument_id, price, quantity, order_type, stop_loss=None):
        return 'price'

    def buy_at_market_price(self, instrument_id, quantity, order_type, stop_loss=None):
        return 'price'

    def sell(self, instrument_id, price, quantity, order_type, stop_loss=None):
        return 'price'

    def sell_at_market_price(self, instrument_id, quantity, order_type, stop_loss=None):
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
        request_token = self.get_request_token()
        data = self.con.generate_session(request_token, api_secret=settings.KITE['API_SECRET'])
        # access_token = data["access_token"]
        self.con.set_access_token(data["access_token"])
        # self.ticker = KiteTicker(api_key=settings.KITE['API_KEY'], access_token=access_token)

    def get_quote(self, instrument_id):
        return self.con.quote(instrument_id)

    def get_open_price(self, instrument, date=None):
        if not settings.DEBUG:
            date = datetime.today().date()
        data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                        to_date=date + timedelta(days=1),
                                        interval='day')
        return data['open']

    def get_minute_candles(self, instrument_id, from_date, to_date):
        pass

    def get_daily_candles(self, instrument_id, from_date, to_date):
        return self.con.historical_data(instrument_token=instrument_id, from_date=from_date,
                                        to_date=to_date,
                                        interval='minute')

    def get_top_gainers(self, date, number=5):
        data = self.get_nifty50_sorted_by_change(date=date)
        if len(data) >= number:
            return data[-number:].reverse()

    def get_nifty50_sorted_by_change(self, date):
        total_data = []
        for symbol, instrument in settings.NIFTY50.items():
            data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                            to_date=date + timedelta(days=2),
                                            interval='day')
            candle = Candle(data=data[0])
            total_data.append((instrument, symbol, 100.0 * (candle.close - candle.open) / candle.open), )
        return sorted(total_data, key=lambda x: x[2])

    def get_top_losers(self, date, number=5):
        data = self.get_nifty50_sorted_by_change(date=date)
        if len(data) >= number:
            return data[:number]

    def get_nifty50_stocks(self):
        for symbol, instrument in settings.NIFTY50.items():
            conn = psycopg2.connect(host=settings.DATABASE['HOST'], database=settings.DATABASE['NAME'],
                                    user=settings.DATABASE['USERNAME'], password=settings.DATABASE['PASSWORD'])
            cur = conn.cursor()
            result = cur.execute('SELECT * FROM instrument WHERE instrument=%', [instrument])
            data = result.fetchone()[0]
            print(data)
            # Stock(id=data[0], name, symbol, instrument, instrument_type, tick_size, exchange)

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
        con = SeleniumConnector(is_headless=False)
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
        return request_token


class Transaction(object):
    """
    This class holds one transaction to be made for profit, suggested by the algorithm
    Args
        type: buy/sale
        stock: Stock instance
        thread_interval: interval for thread in seconds
    """
    thread_interval = 30

    def __init__(self, type, stock, trigger_change, quantity, target_change, stop_loss_percent, date_time=None):
        self.type = type
        self.stock = stock
        self.trigger_change = trigger_change
        self.target_change = target_change
        self.stop_loss_percent = stop_loss_percent
        self.stock_history = KiteHistory(exchanges='NSE')
        self.stock_app = KiteConnect(exchanges='NSE')
        self.transaction_price = None
        self.transaction_close_price = None
        self.trigger_success = None
        self.trigger_price = None
        self.close_success = None
        if not settings.DEBUG:
            self.open_price = self.stock_history.get_open_price(date=date_time.date())
        else:
            self.open_price = self.stock_history.get_open_price()
        if type == 'buy':
            self.transaction_price = self.stock_app.buy_at_market_price(instrument_id=stock.instrument,
                                                                        quantity=quantity, order_type='market',
                                                                        stop_loss=stop_loss_percent)
        elif type == 'sale':
            self.transaction_price = self.stock_app.sell_at_market_price(instrument_id=stock.instrument,
                                                                         quantity=quantity, order_type='market',
                                                                         stop_loss=stop_loss_percent)
        else:
            raise NotImplemented
        assert bool(self.transaction_price)
        self.thread_factory = ThreadFactory(runner=self.wait_for_trigger, interval=self.thread_interval)
        self.thread_factory.start()

    def wait_for_trigger(self):
        assert bool(self.trigger_change)
        quote = self.stock_history.get_quote(self.stock.instrument)
        if self.type == 'buy':
            if quote.price >= (self.open_price * (100 + self.trigger_change)):
                self.trigger_success = True
        elif self.type == 'sale':
            if quote.price <= (self.open_price * (100 - self.target_change)):
                self.trigger_success = True
        if self.trigger_success is not None and self.trigger_success:
            self.trigger_price = self.stock_app.sell_at_market_price(instrument_id=self.stock.instrument,
                                                                     quantity=self.quantity,
                                                                     order_type='market', stop_loss=None)
            self.thread_factory.runner = self.wait_for_square_off
        return True

    def wait_for_square_off(self):
        assert bool(self.transaction_price)
        quote = self.stock_history.get_quote(self.stock.instrument)
        if self.type == 'buy':
            if quote.price >= (self.trigger_price * (100 + self.target_change)):
                self.close_success = True
            elif quote.price < (self.trigger_price * (100 - self.stop_loss_percent)):
                self.close_success = False
        elif self.type == 'sale':
            if quote.price <= (self.trigger_price * (100 - self.target_change)):
                self.close_success = True
            elif quote.price > (self.trigger_price * (100 + self.stop_loss_percent)):
                self.close_success = False
        if self.close_success is not None:
            self.transaction_price = self.stock_app.sell_at_market_price(instrument_id=self.stock.instrument,
                                                                         quantity=self.quantity,
                                                                         order_type='market', stop_loss=None)
            self.close_transaction()
        return True

    def close_transaction(self):
        assert self.close_success is not None
        self.thread_factory.stopper = True


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
        self.stock_history = KiteHistory(exchanges='NSE')
        super(OpenDoors, self).__init__(settings=settings)

    def start_algorithm(self):
        if settings.DEBUG:
            date = self.date
        else:
            date = datetime.now().date() - timedelta(days=1)
        stocks = self.stock_history.get_nifty50_sorted_by_change(date=date)
        gainers = stocks[-5:]
        gainers.reverse()
        losers = stocks[:5]
        transactions = []
        for stock in (gainers + losers):
            trans = Transaction()
            # Buy the stock when it reaches the condition and then sell at target
        # Start tracking gainers for the target decrease from opening
        # Start tracking losers for the target increase from opening

    def create_trigger(self, Stock):
        pass


x = KiteHistory(exchanges='NSE')
x.get_nifty50_stocks()
