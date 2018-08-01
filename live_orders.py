import csv
import datetime
import math
import os
import time

import redis

from helpers import get_previous_open_date
from zerodha import KiteHistory

r = redis.StrictRedis(host='localhost', port=6379)


class OpenDoor(object):
    FILTER_STATUS_PN = 'pending'
    FILTER_STATUS_FL = 'failure'
    FILTER_STATUS_SC = 'success'
    EXP_TYPE_GN = 'gainer'
    EXP_TYPE_LS = 'loser'

    def __init__(self, logger,
                 configuration={'change': .2,
                                'stop_loss': 1.0,
                                'amount': 500000.00,
                                'max_change': .54,
                                'open_price': datetime.time(hour=7, minute=12, second=5),
                                'start_trading': datetime.time(hour=7, minute=14, second=58),
                                'end_trading': datetime.time(hour=9, minute=15, second=10),
                                'target_change': .6}):
        self.logger = logger
        self.logger.info('init OpenDoor')
        self.today_date = datetime.datetime.now().date()
        self.c = configuration
        self.success_rate = 0
        self.master_profit = 0
        self.stock_history = KiteHistory(exchange='NSE', logger=self.logger)
        self.file_name = os.path.join('data', 'report_' + str(self.today_date) + '.csv')
        self.fields = ['symbol', 'date', 'previous_close', 'open', 'type', 'trigger_price', 'target_price',
                       'investment', 'return', 'profit', 'stop_loss_price', 'high', 'low', 'result', ]
        self.nifty50 = self.stock_history.get_nifty50_stocks()
        self.nifty50_close = {}
        self.nifty50_open = {}
        self.filtered_stocks = {}
        while len(self.nifty50_close) != len(self.nifty50):
            self.set_nifty50_previous_day_close()
            self.logger.info('Setting close price.')
            time.sleep(1)
        self.write_file_row('price,target_price,stop_loss,trans_type,quantity,order_id')
        self.logger.info('init OpenDoor ended.')

    def clean_redis(self):
        all_keys = r.hgetall('get_minutes_candles')
        for key, value in all_keys.iteritems():
            r.hdel('get_minutes_candles', key)

    def set_nifty50_previous_day_close(self):
        if len(self.nifty50_close) == len(self.nifty50):
            return
        for stock in self.nifty50:
            self.get_stock_previous_close(stock)
        self.logger.info('Previous day close set: {}'.format(self.nifty50_close))

    def set_nifty50_open(self):
        if len(self.nifty50_open) == len(self.nifty50):
            return
        for stock in self.nifty50:
            self.get_stock_open(stock)

    def filter_stocks(self):
        self.logger.info('Start filter')
        self.set_nifty50_open()
        for stock in self.nifty50:
            if stock.symbol not in self.nifty50_open or stock.symbol not in self.nifty50_close:
                self.logger.error("Symbol not in either open or close: stock - {}".format(stock.symbol))
                self.filtered_stocks[stock.symbol] = (self.FILTER_STATUS_PN, None,)
                continue
            change = (self.nifty50_open[stock.symbol] - self.nifty50_close[stock.symbol]) / self.nifty50_close[
                stock.symbol]
            if self.c['change'] / 100.00 <= change <= self.c['max_change'] / 100.00:
                self.filtered_stocks[stock.symbol] = (self.FILTER_STATUS_SC,
                                                      {'stock': stock, 'type': self.EXP_TYPE_GN,
                                                       'open': self.nifty50_open[stock.symbol],
                                                       'prev_close': self.nifty50_close[stock.symbol]},)
            elif -self.c['max_change'] / 100.00 <= change <= -self.c['change'] / 100.00:
                self.filtered_stocks[stock.symbol] = (self.FILTER_STATUS_SC,
                                                      {'stock': stock, 'type': self.EXP_TYPE_LS,
                                                       'open': self.nifty50_open[stock.symbol],
                                                       'prev_close': self.nifty50_close[stock.symbol]},)
            else:
                self.filtered_stocks[stock.symbol] = (self.FILTER_STATUS_FL, None,)
        self.logger.info('End filter. {}'.format(self.filtered_stocks))

    def get_stock_open(self, stock):
        try:
            if stock.symbol not in self.nifty50_open:
                data = self.stock_history.get_nifty50_open_price()
                if str(stock.instrument) in data and data[str(stock.instrument)]:
                    self.nifty50_open[stock.symbol] = data[str(stock.instrument)]
                else:
                    return
        except (IndexError, KeyError) as e:
            self.logger.error('Index Error get open price: {}'.format(e))
            return
        return self.nifty50_open[stock.symbol]

    def get_stock_previous_close(self, stock):
        try:
            if stock.symbol not in self.nifty50_close:
                previous_day = get_previous_open_date(date=self.today_date)
                self.nifty50_close[stock.symbol] = self.stock_history.get_daily_close_price(instrument=stock.instrument,
                                                                                            date=previous_day)
        except IndexError:
            self.logger.error('Error getting previous close for {}, date: {}'.format(stock, previous_day))
            return
        return self.nifty50_close[stock.symbol]

    def filter_one_stock(self, stock):
        if stock.symbol in self.filtered_stocks:
            return self.filtered_stocks[stock.symbol]
        self.get_stock_open(stock)
        if (stock.symbol not in self.nifty50_open) or (stock.symbol not in self.nifty50_close):
            return self.FILTER_STATUS_PN, None
        change = (self.nifty50_open[stock.symbol] - self.nifty50_close[stock.symbol]) / self.nifty50_close[stock.symbol]
        if (self.c['change'] / 100.00) <= change <= (self.c['max_change'] / 100.00):
            transaction_type = self.EXP_TYPE_GN
        elif (-self.c['max_change'] / 100.00) <= change <= (-self.c['change'] / 100.00):
            transaction_type = self.EXP_TYPE_LS
        else:
            self.filtered_stocks[stock.symbol] = (self.FILTER_STATUS_FL, None,)
            return self.filtered_stocks[stock.symbol]
        self.filtered_stocks[stock.symbol] = (self.FILTER_STATUS_SC, {'stock': stock, 'type': transaction_type,
                                                                      'open': self.nifty50_open[stock.symbol],
                                                                      'prev_close': self.nifty50_close[stock.symbol]},)
        return self.filtered_stocks[stock.symbol]

    def run(self):
        self.logger.info('Starting run.')
        in_queue = []
        done = []
        counter = 1
        while datetime.datetime.now().time() < self.c['open_price']:
            self.stock_history.get_access_token()
            self.logger.info("Waiting for open price.")
            time.sleep(1)
        self.set_nifty50_open()
        self.filter_stocks()
        while datetime.datetime.now().time() < self.c['start_trading']:
            self.logger.info("Just waiting!")
            time.sleep(1)
        self.logger.info('Trying for the {}st time.'.format(counter))
        print(self.filtered_stocks)
        for symbol, stock in self.filtered_stocks.iteritems():
            if stock[0] in [self.FILTER_STATUS_PN, self.FILTER_STATUS_FL]:
                self.logger.info('Failed filter: {}, stock: {}'.format(stock[0], stock))
                continue
            stock_details = stock[1]
            if r.get('stock_orders_{}'.format(stock_details['stock'].instrument)):
                self.logger.info('Order already in redis, '
                                 'key: {}'.format('stock_orders_{}'.format(stock_details['stock'].instrument)))
                continue
            if stock_details['stock'].instrument not in in_queue:
                in_queue.append(stock_details['stock'].instrument)
            quote = self.stock_history.get_quote(stock_details['stock'].instrument)
            if not quote:
                self.logger.info('Quote not found. {}'.format(stock_details['stock']))
                continue
            if stock_details['type'] == self.EXP_TYPE_GN:
                price = round(quote[str(stock_details['stock'].instrument)]['depth']['sell'][0]['price'], 2)
            else:
                price = round(quote[str(stock_details['stock'].instrument)]['depth']['buy'][0]['price'], 2)
            target_price = round((self.c['target_change'] / 100.00) * price, 2)
            stop_loss = round((self.c['stop_loss'] / 100.00) * price, 2)
            self.logger.info('Stock: {}, Price: {}, Target: {}, '
                             'Stop loss: {}'.format(stock_details, price, target_price, stop_loss))
            if price == 0:
                self.logger.error('Price coming out to be zero: {}'.format(stock))
                continue
            quantity = int(math.floor(self.c['amount'] / price))
            transaction_type = 'buy' if stock_details['type'] == self.EXP_TYPE_GN else 'sell'
            if quantity > 0:
                order_id = self.stock_history.place_bracket_order_at_market_price(
                    symbol=stock_details['stock'].symbol,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    square_off=target_price,
                    stop_loss=stop_loss,
                    price=price)
                self.logger.info('Order id: {}, Stock: {}'.format(order_id, stock_details))
                self.write_file_row('\n{},{},{},{},{},{}'.format(price, target_price, stop_loss, transaction_type,
                                                                 quantity, order_id))
            r.set('stock_orders_{}'.format(stock.instrument), str(order_id), ex=60 * 60 * 17)
            done.append(stock_details['stock'].instrument)
        self.logger.info('Ending run.')
        return True

    def write_file_row(self, data):
        with open(self.file_name, 'a') as report_file:
            report_file.write(data)

    def write_row(self, data):
        with open(self.file_name, 'a') as report_file:
            csv_writer = csv.DictWriter(report_file, fieldnames=self.fields)
            csv_writer.writerow(data)

    def set_csv_header(self):
        with open(self.file_name, 'w') as report_file:
            csv_writer = csv.DictWriter(report_file, fieldnames=self.fields)
            csv_writer.writeheader()
