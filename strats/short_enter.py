from datetime import datetime
from helpers import get_data, class_model, get_data, short_classifier
from strats import enter
from alpaca.data import TimeFrameUnit

import os
import pandas as pd
import numpy as np

def enter_short(assets, market_client, trading_client, option_client):
    time_window = int(os.getenv('TIME_WINDOW'))
    day_span = int(os.getenv('SHORT_CLASS_DAY_SPAN'))

    positions = get_data.get_positions(trading_client)
    classifications = class_model.classify_symbols(assets, short_classifier.classification, market_client, datetime.now(), TimeFrameUnit.Minute, time_window, day_span)

    for c in classifications:
        enter.enter_position(c, positions, trading_client, market_client, option_client)