"""
This module will hold all the classes related to a stock. This won't have anything to do with exchanges or the
underlying API protocols in use to execute transactions.
"""


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


class Candle(object):
    def __init__(self, data):
        self.volume = data['volume']
        self.high = data['high']
        self.low = data['low']
        self.date = data['date']
        self.close = data['close']
        self.open = data['open']
