def sell_symbol(position, trading_client):
    return trading_client.close_position(position)