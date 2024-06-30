from alpaca.data import TimeFrame, TimeFrameUnit
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta
from alpaca.trading.enums import OrderSide, AssetClass
from alpaca.data.enums import Adjustment,DataFeed
from alpaca.trading.requests import GetOrdersRequest

def get_bars(symbol, start, end, market_client):
    full_data = market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=symbol,
                            start=start,
                            end=end,
                            adjustment=Adjustment.ALL,
                            feed=DataFeed.IEX,
                            timeframe=TimeFrame(amount=5, unit=TimeFrameUnit.Minute)))
    return full_data.df

def get_buying_power(trading_client):
    account = trading_client.get_account()
    return float(account.buying_power)

def check_exit_pdt_gaurd(symbol, trading_client):
    return check_pdt_gaurd(symbol, OrderSide.BUY, trading_client)

def check_enter_pdt_gaurd(symbol, trading_client):
    return check_pdt_gaurd(symbol, OrderSide.SELL, trading_client)

# IF TRUE WE CANT FLIP
def check_pdt_gaurd(symbol, side, trading_client):
    previous_date = datetime.now() - timedelta(hours=13)
    orders = trading_client.get_orders(GetOrdersRequest(status='closed', after=previous_date, side=side))
    stock_orders = sum(1 for o in orders if o.asset_class == AssetClass.US_EQUITY and o.symbol == symbol)
    options_orders = sum(1 for o in orders if o.asset_class == AssetClass.US_OPTION and o.symbol.startswith(symbol))
    return (stock_orders + options_orders) > 0

def check_option_gaurd(trading_client):
    previous_date = datetime.now() - timedelta(hours=13)
    orders = trading_client.get_orders(GetOrdersRequest(status='closed', after=previous_date, side=OrderSide.BUY))
    options_orders = sum(1 for o in orders if o.asset_class == AssetClass.US_OPTION)
    return options_orders > 0