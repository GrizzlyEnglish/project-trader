from alpaca.data import TimeFrame 
from alpaca.data.requests import  CryptoBarsRequest, StockBarsRequest
from alpaca.data.historical import CryptoHistoricalDataClient

def get_bars(symbol, start, end, market_client):
    if (type(market_client) == CryptoHistoricalDataClient):
        full_data = market_client.get_crypto_bars(CryptoBarsRequest(symbol_or_symbols=symbol,
                                start=start,
                                end=end,
                                adjustment='raw',
                                feed='sip',
                                timeframe=TimeFrame.Minute))
    else:
        full_data = market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=symbol,
                                start=start,
                                end=end,
                                adjustment='raw',
                                feed='sip',
                                timeframe=TimeFrame.Minute))
    return full_data.df