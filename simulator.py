import csv
from datetime import timedelta

from helpers import get_previous_open_date
from zerodha import KiteHistory


class OpenDoorsSimulator(object):
    def __init__(self, logger, date, configuration={'change': .5, 'stop_loss': 2.4, 'max_change': .6}):
        self.logger = logger
        self.date = date
        self.c = configuration
        self.stock_history = KiteHistory(exchange='NSE', logger=self.logger)

    def get_nifty50_previous_day_close(self):
        previous_day = get_previous_open_date(date=self.date)
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
                                                                           date=self.date)
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
        result = {'success': 0, 'failures': 0}
        for stock_details in filtered_stocks:
            success = False
            minute_candles = self.stock_history.get_minutes_candles(instrument=stock_details['stock'].instrument,
                                                                    from_date=self.date,
                                                                    to_date=self.date + timedelta(days=1))
            for candle in minute_candles:
                if stock_details['type'] == 'gainer':
                    stop_price = stock_details['open'] * (1 - self.c['stop_loss'] / 100)
                    target_price = stock_details['open'] * (1 + self.c['change'] / 100)
                else:
                    stop_price = stock_details['open'] * (1 + self.c['stop_loss'] / 100)
                    target_price = stock_details['open'] * (1 - self.c['change'] / 100)
                if stock_details['type'] == 'gainer' and candle['close'] <= stop_price:
                    result['failures'] = result['failures'] + 1
                    break
                if stock_details['type'] == 'gainer' and candle['close'] >= target_price:
                    result['success'] = result['success'] + 1
                    success = True
                    break
                if stock_details['type'] == 'loser' and candle['close'] >= stop_price:
                    result['failures'] = result['failures'] + 1
                    break
                if stock_details['type'] == 'loser' and candle['close'] <= target_price:
                    result['success'] = result['success'] + 1
                    success = True
                    break
            result['failures'] = result['failures'] + 1
            self.write_row(data={'symbol': stock_details['stock'].symbol, 'date': str(self.date.date()),
                                 'previous_close': stock_details['prev_close'],
                                 'open': stock_details['open'], 'type': stock_details['type'],
                                 'target_price': target_price, 'stop_loss_price': stop_price,
                                 'result': 'success' if success else 'failure'})
        return result

    def write_row(self, data):
        with open('report.csv', 'a') as report_file:
            csv_writer = csv.DictWriter(report_file)
            csv_writer.write(data)
