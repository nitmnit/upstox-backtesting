from nsepy import get_history
from datetime import date

data = get_history(symbol="SBIN", start=date(2015, 1, 1), end=date(2015, 1, 31))
data[['Close']].plot()
# print(data)

from nsepy.history import get_price_list

prices = get_price_list(dt=date(2015, 1, 1))
print(prices)


class StockAlgorithm(object):
    def get_stock_data(self, symbol, start, end):
        data = get_history(symbol=symbol, start=start, end=end)


x = StockAlgorithm()
x.get_stock_data(symbol='SBIN', start=None, end=None)
