from datetime import timedelta, datetime as ddatetime
import logging.config

import redis

from open_doors import OpenDoors

logger = logging.getLogger(__name__)
r = redis.StrictRedis(host='localhost', port=6379)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,  # this fixes the problem
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s [%(pathname)s:%(lineno)d] - %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'freaky_bananas.log',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 100,
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
})

start_date = ddatetime(year=2018, month=1, day=1, hour=9, minute=15, second=0)
end_date = ddatetime(year=2018, month=6, day=1, hour=9, minute=15, second=0)
current_date = start_date
master_profit = 0
while start_date <= current_date <= end_date:
    x = OpenDoor(date=current_date, logger=logger)
    x.start_algorithm()
    master_profit += x.total_profit
    current_date = current_date + timedelta(days=1)
    while current_date.strftime('%a') in ['Sat', 'Sun']:
        current_date = current_date + timedelta(days=1)
    logger.info('\nMaster Profit \nFrom date: {} \nTo Date: {}\nProfit: {}'.format(start_date, current_date,
                                                                                   master_profit))
