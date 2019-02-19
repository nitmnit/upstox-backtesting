from django.core.management.base import BaseCommand

from helpers import ZerodhaHelper


class Command(BaseCommand):
    help = 'Start stock trading'

    def handle(self, *args, **kwargs):
        ZerodhaHelper.generate_access_token()
