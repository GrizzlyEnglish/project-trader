from alpaca.data import TimeFrame, TimeFrameUnit
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta
from alpaca.trading.enums import OrderSide
from alpaca.trading.requests import GetOrdersRequest

def get_bars(symbol, start, end, market_client):
    full_data = market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=symbol,
                            start=start,
                            end=end,
                            adjustment='raw',
                            feed='sip',
                            timeframe=TimeFrame(amount=5, unit=TimeFrameUnit.Minute)))
    return full_data.df

def get_buying_power(trading_client):
    account = trading_client.get_account()
    return float(account.buying_power)

def position_sellable(symbol, trading_client):
    previous_date = datetime.now() - timedelta(hours=12)
    orders = trading_client.get_orders(GetOrdersRequest(status='closed', after=previous_date, side=OrderSide.BUY, symbols=[symbol])) 
    return len(orders) == 0