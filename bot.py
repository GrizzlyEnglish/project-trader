from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from discord.ext import commands
from src.charts import option_sentiment

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

bot.run(token)