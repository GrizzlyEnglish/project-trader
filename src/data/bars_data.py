from alpaca.trading.enums import OrderSide, AssetClass
from alpaca.data.enums import Adjustment,DataFeed
from alpaca.trading.requests import GetOrdersRequest
from alpaca.data import TimeFrame, TimeFrameUnit
from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest

from src.helpers import features

class BarData:

    def __init__(self, symbol, start, end, market_client) -> None:
        self.symbol = symbol
        self.start = start
        self.end = end
        self.market_client = market_client
        pass

    def get_bars(self, timeframe=1, unit='Min'):
        alp_unit = TimeFrameUnit.Minute

        if unit == 'Hour':
            alp_unit = TimeFrameUnit.Hour

        full_data = self.market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=self.symbol,
                                start=self.start,
                                end=self.end,
                                adjustment=Adjustment.ALL,
                                feed=DataFeed.IEX,
                                timeframe=TimeFrame(amount=timeframe, unit=alp_unit)))
        
        df = full_data.df

        df = features.feature_engineer_bars(df)

        self.df = df

        return df
    