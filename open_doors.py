from datetime import timedelta, datetime

from algorithms import Algorithm, Expectation
from zerodha import KiteHistory


class OpenDoors(Algorithm):
    def __init__(self, logger, opening_increase=.1, opening_decrease=.1, target_increase=1.0, target_decrease=1.0,
                 increase_stop_loss=.1, decrease_stop_loss=.1, time_slot=timedelta(minutes=15), date=None):
        self.logger = logger
        settings = {
            'opening_increase': opening_increase,
            'opening_decrease': opening_decrease,
            'target_increase': target_increase,
            'target_decrease': target_decrease,
            'increase_stop_loss': increase_stop_loss,
            'decrease_stop_loss': decrease_stop_loss,
            'time_slot': time_slot,
        }
        self.date = date
        self.increase_stop_loss = increase_stop_loss
        self.decrease_stop_loss = decrease_stop_loss
        if not date:
            self.date = datetime.now()
        self.stock_history = KiteHistory(exchange='NSE', logger=self.logger)
        self.transactions = []
        super(OpenDoors, self).__init__(settings=settings)

    def start_algorithm(self):
        self.logger.warning('Starting algorithm.')
        self.logger.info('date. {}'.format(self.date))
        stocks = self.stock_history.get_nifty50_sorted_by_change(date=self.date)
        gainers = stocks[-1:]
        gainers.reverse()
        losers = stocks[:1]
        for stock in (gainers + losers):
            trans = Expectation(logger=self.logger, type='buy', stock=stock[0], trigger_change=.1, amount=10000,
                                target_change=.5, stop_loss_percent=self.increase_stop_loss, date_time=self.date)
            self.transactions.append(trans)
            trans = Expectation(logger=self.logger, type='sell', stock=stock[0], trigger_change=.1, amount=10000.0,
                                target_change=.5, stop_loss_percent=self.decrease_stop_loss, date_time=self.date)
            self.transactions.append(trans)
            self.logger.info('Created {} transactions.'.format(len(self.transactions)))
        self.stop_algorithm()

    def stop_algorithm(self):
        self.logger.info('Stop Algorithm.')
        stoppers = [False]
        previous_stopper = stoppers
        while not all(stoppers):
            stoppers = []
            for index in range(len(self.transactions)):
                stoppers.append(self.transactions[index].thread_factory.stopper)
            time.sleep(10)
            if stoppers != previous_stopper:
                self.logger.info('Stopper: {}'.format(stoppers))
                previous_stopper = stoppers
        self.total_profit = 0
        for trans in self.transactions:
            self.total_profit += trans.price_result
        self.logger.info('Final profit: {}'.format(self.total_profit))
