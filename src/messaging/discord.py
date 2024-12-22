from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime, timezone

import os

def send_alpaca_message(message):
    alpaca_discord_url = os.getenv('ALPACA_DISCORD_URL')
    print(message)
    #discord = DiscordWebhook(alpaca_discord_url, content=message, rate_limit_retry=True)
    #discord.execute()

def send_stock_message(message):
    alpaca_discord_url = os.getenv('STOCK_DISCORD_URL')
    #discord = DiscordWebhook(alpaca_discord_url, content=message, rate_limit_retry=True)
    #discord.execute()

def create_symbol_weight_message(entries):
    lines = []
    for e in entries:
        lines.append('%s \t Weight: %s' % (e['symbol'], e['weight']))

    return '\n'.join([l for l in lines])

def send_stock_info_messages(enter_entries, exit_entries):
    enter_entries = enter_entries[0:10]
    exit_entries = exit_entries[0:10]

    enter_list = create_symbol_weight_message(enter_entries)
    exit_list = create_symbol_weight_message(exit_entries)

    utc_dt = datetime.now(timezone.utc)
    local_dt = utc_dt.astimezone()

    title = local_dt.strftime('%H:%M:%S')
    body = "TOP 10 Entries\n\n %s \n\nTop 10 Exits\n\n %s" % (enter_list, exit_list)
    stock_discord_url = os.getenv('STOCK_DISCORD_URL')
    discord = DiscordWebhook(stock_discord_url)
    embed = DiscordEmbed(title=title, description=body)
    discord.add_embed(embed)
    discord.execute()