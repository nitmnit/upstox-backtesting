from django.core.management.base import BaseCommand

from helpers import ZerodhaWebHelper


class Command(BaseCommand):
    help = 'Start stock trading'

    def handle(self, *args, **kwargs):
        ZerodhaWebHelper().generate_access_token()
