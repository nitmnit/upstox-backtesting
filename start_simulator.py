from datetime import timedelta, datetime as ddatetime
import logging.config

import redis

from simulator import OpenDoorsSimulator

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
end_date = ddatetime(year=2018, month=1, day=10, hour=9, minute=15, second=0)
current_date = start_date
master_profit = 0
success_rate = 0
master_result = {'success': 0, 'failures': 0}
while start_date <= current_date <= end_date:
    try:
        x = OpenDoorsSimulator(date=current_date, logger=logger)
        results = x.run_analysys()
        master_result['success'] = master_result['success'] + results['success']
        master_result['failures'] = master_result['failures'] + results['failures']
        logger.info('\nDate: {}, Result: {}, Master Result: {}'.format(current_date, results, master_result))
        if master_result['success'] + master_result['failures'] != 0:
            success_rate = master_result['success'] * 100 / (master_result['success'] + master_result['failures'])
        logger.info('\nSuccess Rate: {}'.format(success_rate))
    except Exception as e:
        logger.info('Exception Date: {}'.format(current_date))
        logger.info('Exception: {}'.format(e))
        raise e
    finally:
        current_date = current_date + timedelta(days=1)
        while current_date.strftime('%a') in ['Sat', 'Sun']:
            current_date = current_date + timedelta(days=1)

logger.info('\nFrom Date: {}\nToDate: {}\Result: {}'.format(start_date, end_date, results))
