import csv
import os
import time
from datetime import datetime
import pytz
from urllib import parse

import requests
from django.conf import settings
from kiteconnect import KiteConnect, KiteTicker
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from freaks.models import Credential, SecurityQuestion, Instrument
from zedi.tasks import save_quotes


class ChromeBrowser:
    def __init__(self):
        chrome_options = Options()
        if settings.ZE_IS_HEADLESS == "true":
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('window-size=1920,1080')
        # chrome_options.add_argument("download.default_directory=C:/Users/Administrator/PycharmProjects/Stock/downloads")
        # prefs = {'download.default_directory': 'C:/Users/Administrator/PycharmProjects/Stock/downloads'}
        # chrome_options.add_experimental_option('prefs', prefs)
        desired_capabilities = DesiredCapabilities.CHROME
        desired_capabilities['loggingPrefs'] = {"browser": "SEVERE"}
        self.driver = webdriver.Chrome(executable_path='chromedriver',
                                       desired_capabilities=DesiredCapabilities.CHROME, chrome_options=chrome_options)
        self.wait_time = 3


class ZerodhaHelper:
    @staticmethod
    def generate_access_token():
        chrome = ChromeBrowser()
        zerodha_credentials = Credential.objects.filter(name='Zerodha').first()
        kite = KiteConnect(api_key=zerodha_credentials.api_key)
        chrome.driver.get(kite.login_url())
        WebDriverWait(chrome.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')))
        username_input = chrome.driver.find_element_by_css_selector('input[type="text"]')
        password_input = chrome.driver.find_element_by_css_selector('input[type="password"]')
        submit_button = chrome.driver.find_element_by_css_selector('button[type="submit"]')
        username_input.send_keys(zerodha_credentials.client_id)
        password_input.send_keys(zerodha_credentials.password)
        submit_button.click()
        WebDriverWait(chrome.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".twofa-form input")))
        pin_el = chrome.driver.find_element_by_css_selector(".twofa-form input")
        pin_el.send_keys(str(zerodha_credentials.pin))
        answer_submit_button = chrome.driver.find_element_by_xpath("//button[@type='submit']")
        answer_submit_button.click()
        time.sleep(1)
        request_token = parse.parse_qs(parse.urlparse(chrome.driver.current_url).query)['request_token'][0]
        data = kite.generate_session(request_token, api_secret=zerodha_credentials.api_secret)
        if 'access_token' not in data:
            raise Exception('Token not found.')
        zerodha_credentials.access_token = data['access_token']
        zerodha_credentials.save()
        chrome.driver.close()

    @staticmethod
    def sync_instruments():
        access_token = Credential.objects.filter(name='Zerodha').first().access_token
        headers = {
            'X-Kite-Version': '3',
            'Authorization': 'token api_key:' + access_token
        }
        response = requests.get(settings.INSTRUMENTS_URL, headers=headers)
        file_name = 'instruments.csv'
        with open(file_name, 'w') as file:
            file.write(response.text)
        with open(file_name, 'r') as file:
            instruments = csv.DictReader(file)
            Instrument.objects.all().delete()
            for instrument in instruments:
                expiry_date = datetime.strptime(instrument['expiry'], '%Y-%m-%d') if instrument['expiry'] else None
                expiry_date = expiry_date.replace(tzinfo=pytz.timezone(settings.TIME_ZONE)) if expiry_date else None
                Instrument.objects.create(name=instrument['name'], instrument_token=int(instrument['instrument_token']),
                                          exchange_token=int(instrument['exchange_token']),
                                          trading_symbol=instrument['tradingsymbol'],
                                          last_price=float(instrument['last_price']),
                                          expiry=expiry_date, strike=float(instrument['strike']),
                                          tick_size=float(instrument['tick_size']),
                                          lot_size=int(instrument['lot_size']),
                                          instrument_type=instrument['instrument_type'], segment=instrument['segment'],
                                          exchange=instrument['exchange'], )
        os.remove(file_name)


class AbstractZerodhaTicker:
    @staticmethod
    def on_ticks(ws, ticks):
        raise NotImplementedError

    @staticmethod
    def on_connect(ws, response):
        raise NotImplementedError

    @staticmethod
    def on_close(ws, code, reason):
        raise NotImplementedError

    @staticmethod
    def connect(ws, code, reason):
        raise NotImplementedError

    @staticmethod
    def connect():
        zc = Credential.objects.filter(name='Zerodha').first()
        kws = KiteTicker(zc.api_key, zc.access_token)

        def on_ticks(ws, ticks):
            # Callback to receive ticks.
            save_quotes.delay(ticks)

        def on_connect(ws, response):
            ws.subscribe([738561, 5633, 4963, 17388, 1333])
            ws.set_mode(ws.MODE_FULL, [738561, 5633, 4963, 17388, 1333])

        def on_close(ws, code, reason):
            print("Connection closed. {}-{}".format(code, reason))
            ws.stop()

        kws.on_ticks = on_ticks
        kws.on_connect = on_connect
        kws.on_close = on_close
        kws.connect()


class ZerodhaWS:
    @staticmethod
    def connect():
        ZerodhaHelper.generate_access_token()
        zc = Credential.objects.filter(name='Zerodha').first()
        kws = KiteTicker(zc.api_key, zc.access_token)

        def on_ticks(ws, ticks):
            # Callback to receive ticks.
            save_quotes.delay(ticks)

        def on_connect(ws, response):
            ws.subscribe([738561, 5633, 4963, 17388, 1333])
            ws.set_mode(ws.MODE_FULL, [738561, 5633, 4963, 17388, 1333])

        def on_close(ws, code, reason):
            print("Connection closed. {}-{}".format(code, reason))
            ws.stop()

        kws.on_ticks = on_ticks
        kws.on_connect = on_connect
        kws.on_close = on_close
        kws.connect()


class ZerodhaWsSimulator():
    pass
