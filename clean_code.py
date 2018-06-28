import datetime
import time
from abc import abstractmethod
from threading import Thread

total_amount = 100000


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


class KiteConnect(object):
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


class KiteHistory(object):
    def __init__(self, exchanges):
        self.exchanges = exchanges

    def get_quote(self, instrument_id):
        return 'price'

    def get_minute_candles(self, instrument_id, from_date, to_date):
        pass

    def get_daily_candles(self, instrument_id, from_date, to_date):
        pass

    def get_top_losers(self, date, exchange):
        pass

    def get_top_gainers(self, date, exchange):
        pass


class Transaction(object):
    """
    This class holds one transaction to be made for profit, suggested by the algorithm
    Args
        type: buy/sale
        stock: Stock instance
        thread_interval: interval for thread in seconds
    """
    thread_interval = 30

    def __init__(self, type, stock, quantity, target_change, stop_loss_percent):
        self.type = type
        self.stock = stock
        self.target_change = target_change
        self.stop_loss_percent = stop_loss_percent
        self.stock_history = KiteHistory(exchanges='NSE')
        self.stock_app = KiteConnect(exchanges='NSE')
        self.transaction_price = None
        self.transaction_close_price = None
        self.success = None
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
        self.thread_factory = ThreadFactory(runner=self.wait_for_square_off, interval=self.thread_interval)
        self.thread_factory.start()

    def wait_for_square_off(self):
        assert bool(self.transaction_price)
        quote = self.stock_history.get_quote(self.stock.instrument)
        if self.type == 'buy':
            if quote.price >= (self.transaction_price * (100 + self.target_change)):
                self.success = True
            elif quote.price < (self.transaction_price * (100 - self.stop_loss_percent)):
                self.success = False
        elif self.type == 'sale':
            if quote.price <= (self.transaction_price * (100 - self.target_change)):
                self.success = True
            elif quote.price > (self.transaction_price * (100 + self.stop_loss_percent)):
                self.success = False
        if self.success is not None:
            self.transaction_close_price = self.stock_app.sell_at_market_price(instrument_id=self.stock.instrument,
                                                                               quantity=self.quantity,
                                                                               order_type='market', stop_loss=None)
            self.close_transaction()
        return True

    def close_transaction(self):
        assert self.success is not None
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
        if self.start_from <= datetime.datetime.now() <= self.end_at:
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
                 increase_stop_loss=.3, decrease_stop_loss=.3, time_slot=datetime.timedelta(minutes=15)):
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
        gainers = self.stock_history.get_top_gainers()
        losers = self.stock_history.get_top_losers()
        for stock in (gainers + losers):
            pass
            # Buy the stock when it reaches the condition and then sell at target
        # Start tracking gainers for the target decrease from opening
        # Start tracking losers for the target increase from opening

    def create_trigger(self, Stock):
        pass
