from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from discord.ext import commands
from charts import option_sentiment
from helpers import trend_logic
from datetime import datetime, timedelta
from helpers import get_data, features, trend_logic

import os
import discord

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
token = os.getenv('DISCORD_TOKEN')

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='chart')
async def on_message(ctx):
    symbol = ctx.message.clean_content.replace('/chart', '').strip()

    fileName = option_sentiment.create_sentiment_file(symbol, trading_client, market_client)

    await ctx.send(file=discord.File(fileName))

    os.remove(fileName)

@bot.command(name='predict')
async def on_message(ctx):
    symbol = ctx.message.clean_content.replace('/predict', '').strip()

    await ctx.send(f'predicting {symbol} close for tomorrow, this may take a moment')

    price = trend_logic.get_predicted_price(symbol, market_client)
    price = '${:,.2f}'.format(price)

    await ctx.send(f'{symbol} predicted closing for tomorrow to be {price}')

@bot.command(name='ressup')
async def on_message(ctx):
    symbol = ctx.message.clean_content.replace('/ressup', '').strip()

    start = datetime.now()
    until = start - timedelta(days=7)

    full_bars = get_data.get_bars(symbol, until, start, market_client)

    if full_bars.empty:
        await ctx.send("Something funky I can't figure it out")

    full_bars = features.feature_engineer_df(full_bars)

    resistance = full_bars['resistance'].iloc[-1]
    support = full_bars['support'].iloc[-1]

    resistance = '${:,.2f}'.format(resistance)
    support = '${:,.2f}'.format(support)

    await ctx.send(f'{symbol} last 7 days has {resistance} and {support}')

@bot.command(name='weight')
async def on_message(ctx):
    symbol = ctx.message.clean_content.replace('/weight', '').strip()

    await ctx.send(f'generating weight and tomorrow close for {symbol}, this may take a moment')

    weight = trend_logic.weight_symbol_current_status([symbol], market_client, datetime.now(), True)[0]

    current_weight = weight['weight']
    predicted_price = weight['predicted_price']

    predicted_price = '${:,.2f}'.format(predicted_price)

    await ctx.send(f'{symbol} current weight is {current_weight} and predicted tomorrow close of {predicted_price}')

bot.run(token)