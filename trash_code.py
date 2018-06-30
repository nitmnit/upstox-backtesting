from datetime import datetime

from clean_code import ThreadFactory


class StockTracker(object):
    """
    This class will track for a particular stock price goal and will call a success callback when successfully done,
    else call failure callback.
    Args:
        target: targetting price/volume
        type: type of the target: increase, decrease, change
        target_type_value: what's the change being targetted
        success: callback called when success, must take all kwargs
        failure: callback called when failure, must take all kwargs
    """
    TYPE_CHOICES = ['change']
    TARGET_CHOICES = ['price', 'volume']
    CHECK_INTERVAL = 30  # In seconds

    def __init__(self, target, type, target_type_value, start_from, end_at, success, failure):
        if type not in self.TYPE_CHOICES:
            raise Exception('Type choice for stock tracker not valid.')
        if target not in self.TARGET_CHOICES:
            raise Exception('Target not a valid choice.')
        self.target = target
        self.type = type
        self.success = success
        self.failure = failure
        self.target_type_value = target_type_value
        self.start_from = start_from
        self.end_at = end_at
        self.thread_factory = ThreadFactory(runner=self.start_tracking, interval=self.CHECK_INTERVAL)
        self.thread_factory.start()

    def start_tracking(self):
        if self.start_from <= datetime.now() <= self.end_at:
            if self.validate():
                self.success()
                self.thread_factory.stopper = True
            return True
        self.failure()
        self.thread_factory.stopper = True
        return True

    def validate(self):
        return False
