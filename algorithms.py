from abc import abstractmethod


class Algorithm:
    pass


class AlgorithmTester:
    """
    This class will help test any given algorithm for it's efficacy by
    giving me returns in a given time period for invested money
    """

    def __init__(self):
        pass

    def run(self, start, end):
        """
        Start running the simulation
        start: start date time to start simulation from
        end: end date time
        """
        pass

    def trigger(self):
        pass


class BaseBrokerData:
    """
    This is a base broker data class which will fetch the data for requested instrument for a given period
    """
    pass


class AbstractAlgorithm:
    """
    This is base algorithm class from which other algorithms will be derived
    """

    def __init__(self):
        pass

    @abstractmethod
    def start(self):
        pass

    def trigger_order(self, instrument_id, order_type, transaction_type, quantity, transaction_price, square_off_price):
        """
        :param instrument_id: id of the instrument as in Instrument models
        :param order_type: type of order intraday etc.
        :param transaction_type: buy/sale transaction type
        :param quantity: number of stocks to buy
        :param transaction_price: order execution at this price
        :param square_off_price: expected price to be reached
        :return: order_id if succeeded otherwise error message
        """
        raise NotImplementedError


class FirstAlgorithm(AbstractAlgorithm):
    def __init__(self):
        pass
