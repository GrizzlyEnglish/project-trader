from src.classifiers import overnight
from src.helpers import get_data, class_model
from datetime import datetime
from src.strats import enter
from alpaca.data import TimeFrameUnit

def enter_overnight(symbol_info, market_client, trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    classifications = class_model.classify_symbols(symbol_info, overnight.classification, market_client, datetime.now(), TimeFrameUnit.Hour)

    for c in classifications:
        enter.enter_position(c, positions, trading_client, market_client, option_client)