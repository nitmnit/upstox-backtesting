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
            time.sleep(1)
            return func(*args, **kwargs)

    return wrapper
