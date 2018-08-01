import psycopg2
import time
from datetime import datetime, timedelta
from requests import ReadTimeout

from kiteconnect.exceptions import NetworkException

import settings


def get_date():
    if settings.DEBUG:
        if datetime.today().strftime("%a") not in ['Sat', 'Sun']:
            return datetime.today().date()
        else:
            return (datetime.today() - timedelta(days=2)).date()


def get_previous_open_date(date):
    date = date - timedelta(days=1)
    if date.strftime("%a") == 'Sat':
        date = date - timedelta(days=1)
    elif date.strftime("%a") == 'Sun':
        date = date - timedelta(days=2)
    return date


def wait_response(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ReadTimeout, NetworkException) as e:
            if kwargs.get('logger', False):
                kwargs['logger'].error('Got error: {}'.format(e))
            else:
                print('Got error: {}'.format(e))
            time.sleep(.3)
            return wrapper(*args, **kwargs)

    return wrapper


def push_instruments_to_database():
    from zerodha import KiteHistory
    con = psycopg2.connect(host=settings.DATABASE['HOST'], database=settings.DATABASE['NAME'],
                           user=settings.DATABASE['USERNAME'],
                           password=settings.DATABASE['PASSWORD'])

    cur = con.cursor()
    instruments = KiteHistory().con.instruments(exchange='NSE')
    for instrument in instruments:
        cur.execute('INSERT INTO instrument (symbol, instrument, instrument_type, tick_size, name, exchange) '
                    'VALUES(\'{}\',{},\'{}\',{},\'{}\',\'{}\')'.format(instrument['tradingsymbol'],
                                                                       instrument['instrument_token'],
                                                                       instrument['instrument_type'],
                                                                       instrument['tick_size'],
                                                                       instrument['name'].replace('\'', ''),
                                                                       instrument['exchange']))
    con.commit()
