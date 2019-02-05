import time
from urllib import parse

from django.conf import settings
from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from freaks.models import Credential, SecurityQuestion


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


class ZerodhaWebHelper:
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
            EC.presence_of_element_located((By.CSS_SELECTOR, '.twofa-form > div:nth-child(3) input')))
        sq1_el = chrome.driver.find_element_by_css_selector('.twofa-form > div:nth-child(2) input')
        sq2_el = chrome.driver.find_element_by_css_selector('.twofa-form > div:nth-child(3) input')
        question1 = sq1_el.get_attribute('label')
        question2 = sq2_el.get_attribute('label')
        answer1 = SecurityQuestion.objects.filter(question__in=question1.replace('?', '').split(' ')).first().answer
        answer2 = SecurityQuestion.objects.filter(question__in=question2.replace('?', '').split(' ')).first().answer
        sq1_el.send_keys(answer1)
        sq2_el.send_keys(answer2)
        answer_submit_button = chrome.driver.find_element_by_css_selector('button[type="submit"]')
        answer_submit_button.click()
        time.sleep(3)
        request_token = parse.parse_qs(parse.urlparse(chrome.driver.current_url).query)['request_token'][0]
        chrome.driver.close()
        data = kite.generate_session(request_token, api_secret=zerodha_credentials.api_secret)
        if 'access_token' not in data:
            raise Exception('Token not found.')
        zerodha_credentials.access_token = data['access_token']
        zerodha_credentials.save()
