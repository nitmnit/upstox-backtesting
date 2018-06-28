from datetime import datetime, timedelta
import time
import urlparse

import pytz
from kiteconnect import KiteConnect

import settings
from clean_code import SeleniumConnector


class Candle(object):
    def __init__(self, data):
        self.volume = data['volume']
        self.high = data['high']
        self.low = data['low']
        self.date = data['date']
        self.close = data['close']
        self.open = data['open']


class KiteHistory(object):

    def __init__(self, exchanges):
        self.exchanges = exchanges
        self.con = KiteConnect(api_key=settings.KITE['API_KEY'])
        request_token = self.get_request_token()
        data = self.con.generate_session(request_token, api_secret=settings.KITE['API_SECRET'])
        # access_token = data["access_token"]
        self.con.set_access_token(data["access_token"])
        # self.ticker = KiteTicker(api_key=settings.KITE['API_KEY'], access_token=access_token)

    def get_quote(self, instrument_id):
        return 'price'

    def get_open_price(self, instrument, date=None):
        if not settings.DEBUG:
            date = datetime.today().date()
        data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                        to_date=date + timedelta(days=1),
                                        interval='day')
        return data['open']

    def get_minute_candles(self, instrument_id, from_date, to_date):
        pass

    def get_daily_candles(self, instrument_id, from_date, to_date):
        return self.con.historical_data(instrument_token=instrument_id, from_date=from_date,
                                        to_date=to_date,
                                        interval='minute')

    def get_top_gainers(self, date, number=5):
        data = self.get_nifty50_sorted_by_change(date=date)
        if len(data) >= number:
            return data[-number:].reverse()

    def get_nifty50_sorted_by_change(self, date):
        total_data = []
        for symbol, instrument in settings.NIFTY50.items():
            data = self.con.historical_data(instrument_token=instrument, from_date=date,
                                            to_date=date + timedelta(days=2),
                                            interval='day')
            candle = Candle(data=data[0])
            total_data.append((instrument, symbol, 100.0 * (candle.close - candle.open) / candle.open), )
        return sorted(total_data, key=lambda x: x[2])

    def get_top_losers(self, date, number=5):
        data = self.get_nifty50_sorted_by_change(date=date)
        if len(data) >= number:
            return data[:number]

    def get_nifty50_stocks(self):
        pass

    @staticmethod
    def get_answer(question):
        if 'career' in question:
            answer = 'ims'
        elif 'watch' in question:
            answer = 'timex'
        elif 'mobile' in question:
            answer = 'sony'
        elif 'birth' in question:
            answer = 'dungarpur'
        elif 'shoe' in question:
            answer = '11'
        else:
            raise Exception('No answer found.')
        return answer

    def get_request_token(self):
        con = SeleniumConnector()
        con.driver.get(self.con.login_url())
        time.sleep(3)
        username_input = con.driver.find_element_by_css_selector('input[type="text"]')
        password_input = con.driver.find_element_by_css_selector('input[type="password"]')
        submit_button = con.driver.find_element_by_css_selector('button[type="submit"]')
        username_input.send_keys(settings.KITE['USERNAME'])
        password_input.send_keys(settings.KITE['PASSWORD'])
        submit_button.click()
        time.sleep(5)
        sq1_el = con.driver.find_element_by_css_selector('.twofa-form > div:nth-child(2) input')
        sq2_el = con.driver.find_element_by_css_selector('.twofa-form > div:nth-child(3) input')
        question1 = sq1_el.get_attribute('label')
        question2 = sq2_el.get_attribute('label')
        answer1 = self.get_answer(question1)
        answer2 = self.get_answer(question2)
        sq1_el.send_keys(answer1)
        sq2_el.send_keys(answer2)
        answer_submit_button = con.driver.find_element_by_css_selector('button[type="submit"]')
        answer_submit_button.click()
        time.sleep(3)
        parsed = urlparse.urlparse(con.driver.current_url)
        request_token = urlparse.parse_qs(parsed.query)['request_token'][0]
        con.driver.close()
        return request_token


kite = KiteHistory(exchanges='NSE')
TIME_ZONE = 'Asia/Kolkata'
india_timezone = pytz.timezone(TIME_ZONE)
date = datetime(2018, 6, 21, 9, 0, 0, 0, india_timezone)
print(kite.get_top_losers(date=date))
print(kite.get_top_gainers(date=date))
