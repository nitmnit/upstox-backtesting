class Brokers:
    UPSTOX = "upstox"
    ZERODHA = "zerodha"


class OrderType:
    BRACKET = "BRACKET_ORDER"


class ProductType:
    INTRADAY = "Intraday"
    DELIVERY = "Delivery"
    COVERORDER = "CoverOrder"
    ONECANCELSOTHER = "OneCancelsOther"


class TransactionType:
    BUY = "Buy"
    SELL = "Sell"


BROKER_CREDENTIALS = {
    Brokers.UPSTOX: {
        "KEY": "",
        "SECRET": "",
        "USERNAME": "",
        "PASSWORD": "8Kw@%y28A0zJ",
        "BIRTH_DATE": "1998",
    }
}


class Exchanges:
    BSE_INDEX = "BSE"
    NSE_INDEX = "NSE"
    BSE_EQ = "BSE Equity"
    BCD_FO = "BSE Currency Futures & Options"
    NSE_EQ = "NSE Equity"
    NSE_FO = "NSE Futures & Options"
    NCD_FO = "NSE Currency Futures & Options"
    MCX_FO = "MCX Futures"


EXCHANGES_CODE = {
    Brokers.UPSTOX: {
        Exchanges.BSE_INDEX: "bse_index",
        Exchanges.NSE_INDEX: "nse_index",
        Exchanges.BSE_EQ: "bse_eq",
        Exchanges.BCD_FO: "bcd_fo",
        Exchanges.NSE_EQ: "nse_eq",
        Exchanges.NSE_FO: "nse_fo",
        Exchanges.NCD_FO: "ncd_fo",
        Exchanges.MCX_FO: "mcx_fo",
    }
}


class AlgorithmRunMode:
    LIVE = 'LIVE'  # To run in live environment with real money
    SEMI_LIVE = 'SEMI_LIVE'  # To run in live environment with virtual money
    SIMULATED_SEMI_LIVE = 'SIMULATED_SEMI_LIVE'  # Virtual environment with historical quotes data with virtual money
    HISTORICAL = 'HISTORICAL'  # Virtual environment with historical minutes data with virtual money
