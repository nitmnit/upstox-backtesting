import csv
import math
from collections import OrderedDict
from datetime import timedelta, time

import settings
from helpers import get_previous_open_date
from zerodha import KiteHistory


class OpenDoorsSimulator(object):
    def __init__(self, logger, from_date, to_date,
                 configuration={'change': .2,
                                'stop_loss': .4,
                                'amount': 1000000,
                                'max_change': .6,
                                'start_trading': time(hour=9, minute=20),
                                'target_change': .2}):
        self.logger = logger
        self.from_date = from_date
        self.current_date = from_date
        self.to_date = to_date
        self.c = configuration
        self.success_rate = 0
        self.master_profit = 0
        self.stock_history = KiteHistory(exchange='NSE', logger=self.logger)
        self.file_name = 'report_' + str(self.from_date) + '_' + str(self.to_date) + '.csv'
        self.master_result = {'success': 0, 'failures': 0, 'square_offs': 0, 'total_profit': 0}
        self.fields = ['symbol', 'date', 'previous_close', 'open', 'type', 'trigger_price', 'target_price',
                       'investment', 'return', 'profit', 'stop_loss_price', 'high', 'low', 'result', ]
        self.set_csv_header()

    def run(self):
        while self.from_date <= self.current_date <= self.to_date:
            try:
                results = self.run_analysys()
                self.master_result['success'] = self.master_result['success'] + results['success']
                self.master_result['failures'] = self.master_result['failures'] + results['failures']
                self.master_result['square_offs'] = self.master_result['square_offs'] + results['square_offs']
                self.master_result['total_profit'] = self.master_result['total_profit'] + results['total_profit']
                self.logger.info('\nDate: {}\nResult: {}\nMaster Result: {}'.format(self.current_date, results,
                                                                                    self.master_result))
                if (self.master_result['success'] + self.master_result['failures'] + self.master_result[
                    'square_offs']) != 0:
                    self.success_rate = self.master_result['success'] * 100 / (
                            self.master_result['success'] + self.master_result['failures']
                            + self.master_result['square_offs'])
                self.logger.info('\nSuccess Rate: {}'.format(self.success_rate))
            except Exception as e:
                self.logger.info('Exception Date: {}'.format(self.current_date))
                self.logger.info('Exception: {}'.format(e))
                # if settings.DEBUG:
                #     raise e
            finally:
                self.current_date = self.current_date + timedelta(days=1)
                while self.current_date.strftime('%a') in ['Sat', 'Sun']:
                    self.current_date = self.current_date + timedelta(days=1)
        self.logger.info('\nFrom Date: {}\nTo Date: {}\Result: {}'.format(self.from_date, self.to_date,
                                                                          self.master_result))

    def get_nifty50_previous_day_close(self):
        previous_day = get_previous_open_date(date=self.current_date)
        nifty50_stocks = self.stock_history.get_nifty50_stocks()
        nifty50_close = {}
        for stock in nifty50_stocks:
            nifty50_close[stock.symbol] = self.stock_history.get_close_price(instrument=stock.instrument,
                                                                             date=previous_day)
        return nifty50_close

    def get_nifty50_open(self):
        nifty50_stocks = self.stock_history.get_nifty50_stocks()
        nifty50_open = {}
        for stock in nifty50_stocks:
            nifty50_open[stock.symbol] = self.stock_history.get_open_price(instrument=stock.instrument,
                                                                           date=self.current_date)
        return nifty50_open

    def filter_stocks(self):
        nifty50_stocks = self.stock_history.get_nifty50_stocks()
        nifty50_close = self.get_nifty50_previous_day_close()
        nifty50_open = self.get_nifty50_open()
        shortlist = []
        for stock in nifty50_stocks:
            change = (nifty50_open[stock.symbol] - nifty50_close[stock.symbol]) / nifty50_close[stock.symbol]
            if self.c['change'] / 100 <= change <= self.c['max_change'] / 100:
                shortlist.append({'stock': stock, 'type': 'gainer', 'open': nifty50_open[stock.symbol],
                                  'prev_close': nifty50_close[stock.symbol]})
            elif -self.c['max_change'] / 100 <= change <= -self.c['change'] / 100:
                shortlist.append({'stock': stock, 'type': 'loser', 'open': nifty50_open[stock.symbol],
                                  'prev_close': nifty50_close[stock.symbol]})
        return shortlist

    def run_analysys(self):
        filtered_stocks = self.filter_stocks()
        result = {'success': 0, 'failures': 0, 'square_offs': 0, 'total_profit': 0}
        for stock_details in filtered_stocks:
            success = None
            minute_candles = self.stock_history.get_minutes_candles(instrument=stock_details['stock'].instrument,
                                                                    from_date=self.current_date,
                                                                    to_date=self.current_date + timedelta(days=1))
            high = 0
            low = 10000000
            trigger_price = None
            closing_price = None
            quantity = math.floor(self.c['amount'] / stock_details['open'])
            for candle in minute_candles:
                if candle['date'].time() < self.c['start_trading']:
                    continue

                if trigger_price is None and stock_details['type'] == 'gainer':
                    trigger_price = candle['low']
                elif trigger_price is None and stock_details['type'] == 'loser':
                    trigger_price = candle['high']

                if candle['date'].time() >= time(hour=15, minute=20):
                    closing_price = candle['close']
                    break
                if candle['high'] > high:
                    high = candle['high']
                if candle['low'] < low:
                    low = candle['low']
                if stock_details['type'] == 'gainer':
                    stop_price = trigger_price * (1 - self.c['stop_loss'] / 100)
                    target_price = trigger_price * (1 + self.c['target_change'] / 100)
                else:
                    stop_price = trigger_price * (1 + self.c['stop_loss'] / 100)
                    target_price = trigger_price * (1 - self.c['target_change'] / 100)
                if stock_details['type'] == 'gainer' and (candle['low'] <= stop_price):
                    success = False
                    closing_price = candle['low']
                    break
                if stock_details['type'] == 'gainer' and candle['high'] >= target_price:
                    success = True
                    closing_price = candle['high']
                    break
                if stock_details['type'] == 'loser' and candle['high'] >= stop_price:
                    success = False
                    closing_price = candle['high']
                    break
                if stock_details['type'] == 'loser' and candle['low'] <= target_price:
                    success = True
                    closing_price = candle['low']
                    break
            if success is None:
                result['square_offs'] = result['square_offs'] + 1
            elif success:
                result['success'] = result['success'] + 1
            elif not success:
                result['failures'] = result['failures'] + 1
            else:
                raise Exception('Unreachable condition reached.')
            profit = closing_price * quantity - trigger_price * quantity
            result['total_profit'] = result['total_profit'] + profit
            self.write_row(
                data=OrderedDict({'symbol': stock_details['stock'].symbol, 'date': str(self.current_date.date()),
                                  'previous_close': stock_details['prev_close'],
                                  'open': stock_details['open'], 'type': stock_details['type'],
                                  'trigger_price': trigger_price,
                                  'target_price': target_price, 'stop_loss_price': stop_price, 'high': high, 'low': low,
                                  'investment': stock_details['open'] * quantity,
                                  'return': closing_price * quantity,
                                  'profit': profit,
                                  'result': 'square_offs' if success is None else 'success'
                                  if success else 'failure'}))
        return result

    def write_row(self, data):
        with open(self.file_name, 'a') as report_file:
            csv_writer = csv.DictWriter(report_file, fieldnames=self.fields)
            csv_writer.writerow(data)

    def set_csv_header(self):
        with open(self.file_name, 'w') as report_file:
            csv_writer = csv.DictWriter(report_file, fieldnames=self.fields)
            csv_writer.writeheader()
