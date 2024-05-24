from alpaca.data import TimeFrame 
from alpaca.data.requests import StockBarsRequest

def get_bars(symbol, start, end, market_client):
    full_data = market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=symbol,
                            start=start,
                            end=end,
                            adjustment='raw',
                            feed='sip',
                            timeframe=TimeFrame.Minute))
    return full_data.df