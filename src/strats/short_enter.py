from datetime import datetime
from src.helpers import get_data, class_model, get_data, short_classifier
from src.strats import enter
from alpaca.data.timeframe import TimeFrameUnit

def enter_short(symbol_info, market_client, trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    classifications = class_model.classify_symbols(symbol_info, short_classifier.classification, market_client, datetime.now(), TimeFrameUnit.Minute)

    for c in classifications:
        enter.enter_position(c, positions, trading_client, market_client, option_client)