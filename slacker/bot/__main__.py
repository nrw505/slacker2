import os
import logging
from dotenv import load_dotenv

from . import Bot

load_dotenv()
logging.basicConfig()

app_token = os.environ.get("SLACK_APP_TOKEN")
bot_token = os.environ.get("SLACK_BOT_TOKEN")
github_token = os.environ.get("GITHUB_TOKEN")
db_url = os.environ.get("DATABASE_URL")

if app_token == None:
    print("SLACK_APP_TOKEN is not set")
if bot_token == None:
    print("SLACK_BOT_TOKEN is not set")
if github_token == None:
    print("GITHUB_TOKEN is not set")
if db_url == None:
    print("DATABASE_URL is not set")

if app_token and bot_token and db_url and github_token:
    bot = Bot(app_token, bot_token, github_token, db_url)
    bot.run()
