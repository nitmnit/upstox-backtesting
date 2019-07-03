from django.core.management.base import BaseCommand

from upstox import UpstoxStockHelper
from freaks import models


class Command(BaseCommand):
    help = 'Start upstox and have fun'

    def handle(self, *args, **kwargs):
        upstox = UpstoxStockHelper()
        stock = models.Instrument.objects.first()
        if stock.instrument_type == "EQ":
            exchange = stock.exchange + "_" + stock.instrument_type
        else:
            exchange = stock.exchange
        data = upstox.get_data(exchange=exchange, symbol=stock.trading_symbol.upper())
        print(data)
