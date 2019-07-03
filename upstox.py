import datetime

import pytz
import requests
import urllib.parse as urlparse
from bs4 import BeautifulSoup
from django.conf import settings
from zedi import constants
from upstox_api.api import Session, Upstox, OHLCInterval

from freaks.models import TempValues


class UpstoxLogin:
    def __init__(self, api_key, api_secret, username, password, birth_date, redirect_uri='http://127.0.0.1'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.username = username
        self.password = password
        self.birth_date = birth_date
        self.session = None
        self.redirect_uri = redirect_uri
        self.login_page_url = "https://api.upstox.com/index/login"
        self.decision_page_url = "https://api.upstox.com/index/dialog/authorize/decision"
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
        }

    def update_access_token(self):
        login_url = self.__get_login_url()
        access_token = self.__get_access_token(login_url)
        self.session.set_code(access_token)
        self.__set_access_token(self.session.retrieve_access_token())

    def __get_login_url(self):
        self.session = Session(self.api_key)
        self.session.set_redirect_uri(self.redirect_uri)
        self.session.set_api_secret(self.api_secret)
        return self.session.get_login_url()

    def __get_transaction_id(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        transaction_id = soup.find('input', {'name': 'transaction_id'}).get('value')
        return transaction_id

    def __set_access_token(self, access_token):
        existing_tokens = TempValues.objects.filter(name=settings.ACCESS_TOKEN_DB_IDENTIFIER).first()
        if existing_tokens:
            existing_tokens.value = access_token
            existing_tokens.save()
            return
        TempValues.objects.create(name=settings.ACCESS_TOKEN_DB_IDENTIFIER, value=access_token)

    def __get_access_token(self, login_url):
        with requests.Session() as session:
            login_page = session.get(login_url, headers=self.headers, )
            login_page.raise_for_status()
            self.headers["content-type"] = "application/x-www-form-urlencoded"
            login_page1 = session.post(self.login_page_url, headers=self.headers, data={
                'apiKey': '',
                'username': self.username,
                'password': self.password,
                'password2fa': self.birth_date,
            })
            login_page1.raise_for_status()
            transaction_id = self.__get_transaction_id(login_page1.content)
            decision_page = session.post(self.decision_page_url, headers=self.headers,
                                         data={"transaction_id": transaction_id})
            if decision_page.status_code != 404:
                raise Exception("Failed to authenticate")
            parsed = urlparse.urlparse(decision_page.url)
            access_token = urlparse.parse_qs(parsed.query)['code'][0]
            return access_token


class UpstoxStockHelper:
    def __init__(self):
        self.client = None
        self.set_client()

    def set_client(self):
        token_data = TempValues.objects.filter(name=settings.ACCESS_TOKEN_DB_IDENTIFIER).first()
        if (not token_data) or (
                token_data.modified < (datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=1))):
            upstox_login_helper = UpstoxLogin(api_key=constants.BROKER_CREDENTIALS[constants.Brokers.UPSTOX]["KEY"],
                                              api_secret=constants.BROKER_CREDENTIALS[constants.Brokers.UPSTOX][
                                                  "SECRET"],
                                              username=constants.BROKER_CREDENTIALS[constants.Brokers.UPSTOX][
                                                  "USERNAME"],
                                              password=constants.BROKER_CREDENTIALS[constants.Brokers.UPSTOX][
                                                  "PASSWORD"],
                                              birth_date=constants.BROKER_CREDENTIALS[constants.Brokers.UPSTOX][
                                                  "BIRTH_DATE"], )
            upstox_login_helper.update_access_token()
        token_data = TempValues.objects.filter(name=settings.ACCESS_TOKEN_DB_IDENTIFIER).first()
        self.client = Upstox(constants.BROKER_CREDENTIALS[constants.Brokers.UPSTOX]["KEY"], token_data.value)
        self.set_master_contracts()

    def set_master_contracts(self):
        self.client.get_master_contract('NSE_EQ')  # get contracts for NSE EQ
        # self.client.get_master_contract('NSE_FO')  # get contracts for NSE FO
        self.client.get_master_contract('NSE_INDEX')  # get contracts for NSE INDEX
        self.client.get_master_contract('BSE_EQ')  # get contracts for BSE EQ
        # self.client.get_master_contract('BCD_FO')  # get contracts for BCD FO
        self.client.get_master_contract('BSE_INDEX')  # get contracts for BSE INDEX
        # self.client.get_master_contract('MCX_INDEX')  # get contracts for MCX INDEX
        # self.client.get_master_contract('MCX_FO')  # get contracts for MCX FO

    def get_data(self, exchange, symbol):
        instrument = self.client.get_instrument_by_symbol(exchange, symbol)
        if instrument is None:
            raise Exception("instrument not found")
        return self.client.get_ohlc(instrument, OHLCInterval.Minute_10,
                                    datetime.datetime.strptime('01/06/2019', '%d/%m/%Y'),
                                    datetime.datetime.strptime('07/06/2019', '%d/%m/%Y'))
