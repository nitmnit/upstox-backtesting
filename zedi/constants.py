class Brokers:
    UPSTOX = "upstox"
    ZERODHA = "zerodha"


BROKER_CREDENTIALS = {
    Brokers.UPSTOX: {
        "KEY": "f08dWVMwbd47WcSN5fL9P6tSaWW2GUsd8FLPrzDr",
        "SECRET": "vckj3ranbl",
        "USERNAME": "",
        "PASSWORD": "8Kw@%y28A0zJ",
        "BIRTH_DATE": "1991",
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
