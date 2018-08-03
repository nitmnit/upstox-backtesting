import logging

from zerodha import KiteHistory

logger = logging.getLogger('test')
x = KiteHistory(logger=logger)
print(x.current_amount())
