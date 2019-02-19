from django.core.management.base import BaseCommand

from helpers import ZerodhaHelper


class Command(BaseCommand):
    help = 'Sync instruments from Zerodha'

    def handle(self, *args, **kwargs):
        ZerodhaHelper.sync_instruments()
