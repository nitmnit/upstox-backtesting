import csv
import datetime
import math
import os
import time

from helpers import get_previous_open_date
from zerodha import KiteHistory


class OpenDoor(object):
    def __init__(self, logger,
                 configuration={'change': .2,
                                'stop_loss': 1,
                                'amount': 20000,
                                'max_change': .5,
                                'start_trading': datetime.time(hour=9, minute=15),
                                'target_change': .6}):
        self.logger = logger
        self.today_date = datetime.datetime.now().date()
        self.c = configuration
        self.success_rate = 0
        self.master_profit = 0
        self.stock_history = KiteHistory(exchange='NSE', logger=self.logger)
        self.file_name = os.path.join('data', 'report_' + str(self.today_date) + '.csv')
        self.fields = ['symbol', 'date', 'previous_close', 'open', 'type', 'trigger_price', 'target_price',
                       'investment', 'return', 'profit', 'stop_loss_price', 'high', 'low', 'result', ]
        self.nifty50 = self.stock_history.get_nifty50_stocks()
        self.write_file_row('price,target_price,stop_loss,trans_type,quantity,profit,order_id')

    def get_nifty50_previous_day_close(self):
        previous_day = get_previous_open_date(date=self.today_date)
        nifty50_close = {}
        for stock in self.nifty50:
            nifty50_close[stock.symbol] = self.stock_history.get_daily_close_price(instrument=stock.instrument,
                                                                                   date=previous_day)
        return nifty50_close

    def get_nifty50_previous_day_close(self):
        previous_day = get_previous_open_date(date=self.today_date)
        nifty50_close = {}
        for stock in self.nifty50:
            nifty50_close[stock.symbol] = self.stock_history.get_daily_close_price(instrument=stock.instrument,
                                                                                   date=previous_day)
        return nifty50_close

    def get_nifty50_open(self):
        nifty50_open = {}
        for stock in self.nifty50:
            nifty50_open[stock.symbol] = self.stock_history.get_daily_open_price(instrument=stock.instrument,
                                                                                 date=self.today_date.date())
        return nifty50_open

    def filter_stocks(self):
        nifty50_close = self.get_nifty50_previous_day_close()
        nifty50_open = self.get_nifty50_open()
        shortlist = []
        for stock in self.nifty50:
            change = (nifty50_open[stock.symbol] - nifty50_close[stock.symbol]) / nifty50_close[stock.symbol]
            if self.c['change'] / 100 <= change <= self.c['max_change'] / 100:
                shortlist.append({'stock': stock, 'type': 'gainer', 'open': nifty50_open[stock.symbol],
                                  'prev_close': nifty50_close[stock.symbol]})
            elif -self.c['max_change'] / 100 <= change <= -self.c['change'] / 100:
                shortlist.append({'stock': stock, 'type': 'loser', 'open': nifty50_open[stock.symbol],
                                  'prev_close': nifty50_close[stock.symbol]})
        return shortlist

    def run(self):
        while datetime.datetime.now().time() < self.c['start_trading']:
            time.sleep(1)
        filtered_stocks = self.filter_stocks()
        self.logger.info(filtered_stocks)
        success = False
        done = []
        while not success:
            for stock_details in filtered_stocks:
                if stock_details['stock'].instrument in done:
                    continue
                quote = self.stock_history.get_quote(stock_details['stock'].instrument)
                if not quote:
                    break
                self.logger.info('Quote Stock{}: Day: {} Quote: {}'.format(stock_details, self.today_date, quote))
                if stock_details['type'] == 'gainer':
                    price = round(quote[str(stock_details['stock'].instrument)]['depth']['sell'][0]['price'], 2)
                else:
                    price = round(quote[str(stock_details['stock'].instrument)]['depth']['buy'][0]['price'], 2)
                target_price = round((self.c['target_change'] / 100) * price, 2)
                stop_loss = round((self.c['stop_loss'] / 100) * price, 2)
                self.logger.info('Stock: {}, Price: {}, Target: {}, '
                                 'Stop loss: {}'.format(stock_details, price, target_price, stop_loss))
                quantity = int(math.floor(self.c['amount'] / price))
                transaction_type = 'buy' if stock_details['type'] == 'gainer' else 'sell'
                if quantity > 0:
                    order_id = self.stock_history.place_bracket_order_at_market_price(
                        symbol=stock_details['stock'].symbol,
                        transaction_type=transaction_type,
                        quantity=quantity,
                        square_off=target_price,
                        stop_loss=stop_loss,
                        price=price)
                    self.logger.info('Order id: {}, Stock: {}'.format(order_id, stock_details))
                done.append(stock_details['stock'].instrument)
                self.write_file_row(
                    '{},{},{},{},{},{},{}'.format(price, target_price, stop_loss, transaction_type, quantity,
                                                  quantity * target_price, order_id))
            success = True
        return None

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
