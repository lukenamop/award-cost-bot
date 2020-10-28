#!/usr/bin/env python3

# import libraries
import os

# postgresql database URL
DB_URL = os.environ['AWC_DATABASE_URL']

# PRAW credentials
R_CLIENT_ID = os.environ['AWC_REDDIT_CLIENT_ID']
R_CLIENT_SECRET = os.environ['AWC_REDDIT_CLIENT_SECRET']
R_PASSWORD = os.environ['AWC_REDDIT_PASSWORD']
R_USERNAME = os.environ['AWC_REDDIT_USERNAME']
R_USER_AGENT = 'u/award-cost-bot (by /u/lukenamop)'
# coin quantity assumption
COIN_QUANT = 1800
# coin price assumption
QUANT_PRICE = 5.99
# legacy gold price $3.99 / $5.99 * 1800 = 1200 coin quantity
GOLD_LEGACY_QUANT = 1200
# legacy gold premium reward
GOLD_LEGACY_PREMIUM = 31
# gold before this timestamp is legacy
GOLD_LEGACY_TIMESTAMP = 1539648000
# list of link blacklist subreddit IDs
LINK_BL_SUB_IDS = ['conspiracy','Coronavirus','nba','pcmasterrace']
# list of banned subreddit IDs
BANNED_SUB_IDS = ['anime','gifs','nextfuckinglevel','RoastMe','gaming','jacksepticeye','news']
# reddit ID to the highest priced submission leaderboard
SUBMISSION_LB_ID = 'euxitc'
# reddit ID to the highest priced comment leaderboard
COMMENT_LB_ID = 'euxinc'
# leaderboard length
AWARD_LB_LENGTH = 20
# number of seconds to sleep upon crashing
CRASH_SLEEP_LENGTH = 5