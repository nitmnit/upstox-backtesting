import csv
import datetime
import math
import os
import time

from helpers import get_previous_open_date
from zerodha import KiteHistory


class OpenDoor(object):
    def __init__(self, logger, from_date, to_date,
                 configuration={'change': .2,
                                'stop_loss': .4,
                                'amount': 20000,
                                'max_change': .34,
                                'start_trading': datetime.time(hour=9, minute=20),
                                'target_change': .4}):
        self.logger = logger
        self.from_date = from_date
        self.current_date = datetime.datetime.now()
        self.to_date = to_date
        self.c = configuration
        self.success_rate = 0
        self.master_profit = 0
        self.stock_history = KiteHistory(exchange='NSE', logger=self.logger)
        self.file_name = os.path.join('data', 'report_' + str(self.from_date) + '_' + str(self.to_date) + '.csv')
        self.master_result = {'success': 0, 'failures': 0, 'square_offs': 0, 'total_profit': 0}
        self.fields = ['symbol', 'date', 'previous_close', 'open', 'type', 'trigger_price', 'target_price',
                       'investment', 'return', 'profit', 'stop_loss_price', 'high', 'low', 'result', ]
        self.set_csv_header()

    def get_nifty50_previous_day_close(self):
        previous_day = get_previous_open_date(date=self.cdt.date())
        nifty50_stocks = self.stock_history.get_nifty50_stocks()
        nifty50_close = {}
        for stock in nifty50_stocks:
            nifty50_close[stock.symbol] = self.stock_history.get_daily_close_price(instrument=stock.instrument,
                                                                                   date=previous_day)
        return nifty50_close

    def run(self):
        # while datetime.datetime.now().time() < datetime.time(hour=9, minute=15):
        #     print('waiting')
        #     time.sleep(1)
        results = self.run_analysys()
        # while self.from_date <= self.current_date <= self.to_date:
        #     try:
        #         results = self.run_analysys()
        #     except Exception as e:
        #         self.logger.info('Exception Date: {}'.format(self.current_date))
        #         self.logger.info('Exception: {}'.format(e))
        #     finally:
        #         self.current_date = self.current_date + datetime.timedelta(days=1)
        #         while self.current_date.strftime('%a') in ['Sat', 'Sun']:
        #             self.current_date = self.current_date + datetime.timedelta(days=1)

    def get_nifty50_previous_day_close(self):
        previous_day = get_previous_open_date(date=self.current_date)
        nifty50_stocks = self.stock_history.get_nifty50_stocks()
        nifty50_close = {}
        for stock in nifty50_stocks:
            nifty50_close[stock.symbol] = self.stock_history.get_daily_close_price(instrument=stock.instrument,
                                                                                   date=previous_day)
        return nifty50_close

    def get_nifty50_open(self):
        nifty50_stocks = self.stock_history.get_nifty50_stocks()
        nifty50_open = {}
        for stock in nifty50_stocks:
            nifty50_open[stock.symbol] = self.stock_history.get_open_price(instrument=stock.instrument,
                                                                           date=self.current_date.date())
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
        self.logger.info(filtered_stocks)
        # if datetime.datetime.now().time() < datetime.time(hour=9, minute=20):
        #     time.sleep(1)
        for stock_details in filtered_stocks:
            quote = self.stock_history.get_quote(stock_details['stock'].instrument)
            if not quote:
                pass
            self.logger.info('Quote Stock{}: Day: {} Quote: {}'.format(stock_details, self.current_date, quote))
            if stock_details['type'] == 'gainer':
                price = quote[str(stock_details['stock'].instrument)]['depth']['sell'][0]['price']
                target_price = (self.c['target_change'] / 100) * price
                stop_loss = (self.c['stop_loss'] / 100) * price
            else:
                price = quote[str(stock_details['stock'].instrument)]['depth']['buy'][0]['price']
                target_price = (self.c['target_change'] / 100) * price
                stop_loss = (self.c['stop_loss'] / 100) * price
            self.logger.info('Stock: {}, Price: {}, Target: {}, '
                             'Stop loss: {}'.format(stock_details, price, target_price, stop_loss))
            quantity = int(math.floor(self.c['amount'] / price))
            transaction_type = 'buy' if stock_details['type'] == 'gainer' else 'sell'
            if quantity > 0:
                order_id = self.stock_history.place_bracket_order_at_market_price(symbol=stock_details['stock'].symbol,
                                                                                  transaction_type=transaction_type,
                                                                                  quantity=quantity,
                                                                                  square_off=target_price,
                                                                                  stop_loss=stop_loss,
                                                                                  price=price)
                self.logger.info('Order id: {}, Stock: {}'.format(order_id, stock_details))
        return None

    def write_row(self, data):
        with open(self.file_name, 'a') as report_file:
            csv_writer = csv.DictWriter(report_file, fieldnames=self.fields)
            csv_writer.writerow(data)

    def set_csv_header(self):
        with open(self.file_name, 'w') as report_file:
            csv_writer = csv.DictWriter(report_file, fieldnames=self.fields)
            csv_writer.writeheader()
