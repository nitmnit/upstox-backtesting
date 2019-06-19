import requests
from django.core.management.base import BaseCommand
from django.conf import settings

from upstox import UpstoxLogin


class Command(BaseCommand):
    help = 'Start upstox and have fun'

    def handle(self, *args, **kwargs):
        upstox_login = UpstoxLogin(api_key=settings.BROKER_CREDENTIALS["UPSTOX"]["KEY"],
                                   api_secret=settings.BROKER_CREDENTIALS["UPSTOX"]["SECRET"],
                                   username=settings.BROKER_CREDENTIALS["UPSTOX"]["USERNAME"],
                                   password=settings.BROKER_CREDENTIALS["UPSTOX"]["PASSWORD"],
                                   birth_date=settings.BROKER_CREDENTIALS["UPSTOX"]["BIRTH_DATE"], )
        upstox_login.login()
