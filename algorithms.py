import math
from abc import abstractmethod
from threading import Thread
import time
from datetime import timedelta, time as ttime

import settings
from zerodha import KiteHistory, KiteCon


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


class IExpectation(object):
    def __init__(self, configuration):
        self.c = configuration

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_end(self):
        pass

    @abstractmethod
    def wait_for_trigger(self):
        pass

    @abstractmethod
    def wait_for_square_off(self):
        pass


class Expectation(object):
    """
    This class holds one transaction to be made for profit, suggested by the algorithm
    Args
        type: buy/sell
        stock: Stock instance
        thread_interval: interval for thread in seconds
    """
    thread_interval = .6
    change_range = 1

    def __init__(self, logger, type, stock, trigger_change, amount, target_change, stop_loss_percent, date_time=None):
        self.logger = logger
        self.logger.info('\nExpectation Date: {}\ntype: {} \nstock: {} \ntrigger_change: {} \nmount: {} '
                         '\ntarget_change: {} \nstop_loss_percent: {} \n'.format(date_time, type, stock, trigger_change,
                                                                                 amount, target_change,
                                                                                 stop_loss_percent))
        self.type = type
        self.stock = stock
        self.trigger_change = trigger_change
        self.target_change = target_change
        self.stop_loss_percent = stop_loss_percent
        self.stock_history = KiteHistory(exchange='NSE', logger=self.logger)
        self.stock_app = KiteCon(exchange='NSE', logger=self.logger)
        self.transaction_price = None  # Price at square off
        self.transaction_close_price = None  # Price at the end of the day
        self.trigger_success = None
        self.trigger_price = None  # Price at trigger
        self.close_success = None
        self.amount = amount
        self.price_result = None
        self.date_time = date_time
        self.open_price = self.stock_history.get_daily_open_price(instrument=self.stock.instrument, date=date_time.date())
        self.time_counter = 0
        self.thread_factory = ThreadFactory(runner=self.wait_for_trigger, interval=self.thread_interval)
        self.thread_factory.start()

    def wait_for_trigger(self):
        assert bool(self.trigger_change)
        if settings.DEBUG:
            time_simulated = self.date_time + timedelta(seconds=self.time_counter)
            if not self.validate_date_time(time_simulated):
                self.logger.info('\nFailed to trigger the price.')
                self.close_transaction()
                return
            quote = self.stock_history.get_minutes_candles(self.stock.instrument, from_date=time_simulated,
                                                           to_date=time_simulated + timedelta(seconds=60 * 2))
            self.time_counter += 60 * 1
            if not quote:
                self.logger.error('\nQuote not found: {}'.format(quote))
                self.close_transaction()
                return True
            price = quote[0]['close']
        else:
            quote = self.stock_history.get_quote(self.stock.instrument)
            price = quote.price
        if self.type == 'buy':
            target_range = (self.open_price * (1 + self.trigger_change / 100),
                            self.open_price * (1 + (self.trigger_change + self.change_range) / 100))
            if target_range[0] <= price <= target_range[1]:
                self.logger.warning('\nBuy trigger successful. Stock: {} '
                                    '\nOpen Price: {} \nBought at: {}'.format(self.stock, self.open_price, price))
                self.trigger_success = True
        elif self.type == 'sell':
            target_range = (self.open_price * (1 - (self.trigger_change + self.change_range) / 100),
                            self.open_price * (1 - self.trigger_change / 100))
            if target_range[0] <= price <= target_range[1]:
                self.logger.warning('\nSell trigger successful. Stock: {} '
                                    '\nOpen Price: {} \nSold at: {}'.format(self.stock, self.open_price, price))
                self.trigger_success = True
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
        if ttime(hour=9, minute=15, second=0) <= date_time.time() <= ttime(hour=15, minute=30, second=0):
            return True
        return False

    def wait_for_square_off(self):
        assert bool(self.trigger_price)
        if settings.DEBUG:
            time_simulated = self.date_time + timedelta(seconds=self.time_counter)
            if not self.validate_date_time(time_simulated):
                self.logger.info('\nFailed to square off the price.')
                self.close_transaction()
            quote = self.stock_history.get_minutes_candles(self.stock.instrument, from_date=time_simulated,
                                                           to_date=time_simulated + timedelta(seconds=60 * 2))
            self.time_counter += 60 * 1
        else:
            quote = self.stock_history.get_quote(self.stock.instrument)
        if not quote:
            self.logger.error('\nQuote not found: {}'.format(quote))
            self.close_transaction()
            return True
        if settings.DEBUG:
            price = quote[0]['close']
        else:
            price = quote.price
        if self.type == 'buy':
            target_range = (self.open_price * (1 - (self.trigger_change + self.change_range) / 100),
                            self.open_price * (1 - self.trigger_change / 100))
            if target_range[0] <= price <= target_range[1]:
                self.close_success = True
                self.logger.warning('\nSell square off successful. Stock: {} '
                                    '\nOpen Price: {} \nSold at: {}'.format(self.stock, self.open_price, price))
            elif price < (self.trigger_price * (1 - self.stop_loss_percent / 100)):
                self.close_success = False
                self.logger.warning('\nSell square off failed. Stock: {} '
                                    '\nOpen Price: {} \nSold at: {}'.format(self.stock, self.open_price, price))
        elif self.type == 'sell':
            target_range = (self.open_price * (1 + self.trigger_change / 100),
                            self.open_price * (1 + (self.trigger_change + self.change_range) / 100))
            if target_range[0] <= price <= target_range[1]:
                self.close_success = True
                self.logger.warning('\nBuy square off successful. Stock: {} '
                                    '\nOpen Price: {} \nBought at: {}'.format(self.stock, self.open_price, price))
            elif price > (self.trigger_price * (1 + self.stop_loss_percent / 100)):
                self.close_success = False
                self.logger.warning('\nBuy square off failed. Stock: {} '
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
        self.transaction_price = price
        self.transaction_close_price = price
        return True

    def close_transaction(self):
        self.logger.error('Closing transaction. {}'.format(self.stock))
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
