import numpy as np
from datetime import timedelta, datetime as ddatetime, time
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

start_date = ddatetime(year=2018, month=7, day=16, hour=9, minute=15, second=0)
start_date = ddatetime(year=2018, month=1, day=1, hour=9, minute=15, second=0)
end_date = ddatetime(year=2018, month=1, day=31, hour=9, minute=15, second=0)
# end_date = ddatetime.now()
# Target change has to be .5
change = ()
configuration = {'change': .2,
                 'stop_loss': .8,
                 'amount': 200000,
                 'max_change': .5,
                 'start_trading': time(hour=9, minute=15),
                 'target_change': .5}

change_range = [.2, .5]
stop_loss_range = [.2, 1.1]
target_change_range = [.2, .7]
for current_change in np.arange(change_range[0], change_range[1], .1):
    for current_stop_loss in np.arange(stop_loss_range[0], stop_loss_range[1], .1):
        for current_target_change in np.arange(target_change_range[0], target_change_range[1], .1):
            configuration = {'change': current_change,
                             'stop_loss': current_stop_loss,
                             'amount': 200000,
                             'max_change': .5,
                             'start_trading': time(hour=9, minute=15),
                             'target_change': current_target_change}
            logger.info('Configuration: {}'.format(configuration))
            print('Configuration: {}'.format(configuration))
            x = OpenDoorsSimulator(from_date=start_date, to_date=end_date, logger=logger, configuration=configuration)
            x.run()
            if current_target_change + .1 < target_change_range[1]:
                current_target_change += .1
            print('Done!')
        if current_stop_loss + .1 < stop_loss_range[1]:
            current_stop_loss += .1
    if current_change + .1 < change_range[1]:
        current_change += .1

# current_date = start_date
# master_profit = 0
# success_rate = 0
# master_result = {'success': 0, 'failures': 0, 'square_offs': 0}
# x = OpenDoorsSimulator(from_date=current_date, to_date=end_date, logger=logger)
# x.set_csv_header(['symbol', 'date', 'previous_close', 'open', 'type', 'target_price', 'stop_loss_price', 'result', ])
# while start_date <= current_date <= end_date:
#     try:
#         x = OpenDoorsSimulator(from_date=current_date, logger=logger,
#                                configuration={'change': .45, 'stop_loss': 2.4, 'max_change': .55})
#         results = x.run_analysys()
#         master_result['success'] = master_result['success'] + results['success']
#         master_result['failures'] = master_result['failures'] + results['failures']
#         master_result['square_offs'] = master_result['square_offs'] + results['square_offs']
#         logger.info('\nDate: {}, Result: {}, Master Result: {}'.format(current_date, results, master_result))
#         if (master_result['success'] + master_result['failures'] + master_result['square_offs']) != 0:
#             success_rate = master_result['success'] * 100 / (master_result['success'] + master_result['failures']
#                                                              + master_result['square_offs'])
#         logger.info('\nSuccess Rate: {}'.format(success_rate))
#     except Exception as e:
#         logger.info('Exception Date: {}'.format(current_date))
#         logger.info('Exception: {}'.format(e))
#     finally:
#         current_date = current_date + timedelta(days=1)
#         while current_date.strftime('%a') in ['Sat', 'Sun']:
#             current_date = current_date + timedelta(days=1)
#
# logger.info('\nFrom Date: {}\nToDate: {}\Result: {}'.format(start_date, end_date, results))
